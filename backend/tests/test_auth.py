from tests.conftest import login


def test_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data
    assert data["user"]["role"] == "admin"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_register_patient(client):
    resp = client.post("/api/auth/register", json={
        "username": "testpatient",
        "email": "tp@test.com",
        "password": "test123",
        "role": "patient",
        "phone": "123456",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "blood_group": "O+",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["user"]["role"] == "patient"


def test_register_duplicate(client):
    client.post("/api/auth/register", json={
        "username": "dup", "email": "dup@test.com", "password": "pass", "role": "patient",
        "phone": "1", "gender": "Male", "date_of_birth": "1990-01-01", "blood_group": "A+",
    })
    resp = client.post("/api/auth/register", json={
        "username": "dup", "email": "dup2@test.com", "password": "pass", "role": "patient",
        "phone": "2", "gender": "Male", "date_of_birth": "1990-01-01", "blood_group": "A+",
    })
    assert resp.status_code == 409


def test_me_endpoint(client):
    token = login(client)
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["username"] == "admin"


def test_patient_profile_clinical_fields_roundtrip(client):
    # Register patient
    resp = client.post("/api/auth/register", json={
        "username": "patclinical",
        "email": "pc@test.com",
        "password": "test123",
        "role": "patient",
        "phone": "123456",
        "gender": "Female",
        "date_of_birth": "1992-02-02",
        "blood_group": "B+",
    })
    assert resp.status_code == 201
    token = resp.get_json()["token"]

    # Update profile with clinical fields
    payload = {
        "allergies": "Penicillin, Dust",
        "chronic_conditions": "Hypertension",
        "emergency_contact_name": "John Doe",
        "emergency_contact_phone": "999999",
        "insurance_provider": "Star Health",
        "insurance_id": "POL-123",
        "height_cm": 170.5,
        "weight_kg": 64.2,
    }
    resp = client.put(
        "/api/patient/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["allergies"] == payload["allergies"]
    assert data["chronic_conditions"] == payload["chronic_conditions"]
    assert data["emergency_contact_name"] == payload["emergency_contact_name"]
    assert data["emergency_contact_phone"] == payload["emergency_contact_phone"]
    assert data["insurance_provider"] == payload["insurance_provider"]
    assert data["insurance_id"] == payload["insurance_id"]
    assert float(data["height_cm"]) == float(payload["height_cm"])
    assert float(data["weight_kg"]) == float(payload["weight_kg"])

    # Fetch profile to confirm persistence
    resp = client.get(
        "/api/patient/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["allergies"] == payload["allergies"]
    assert data["chronic_conditions"] == payload["chronic_conditions"]
