from tests.conftest import login


def test_admin_stats(client):
    token = login(client)
    resp = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "doctors" in data
    assert "patients" in data
    assert "departments" in data


def test_admin_list_departments(client):
    token = login(client)
    resp = client.get("/api/admin/departments", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    depts = resp.get_json()
    assert len(depts) >= 6
    names = [d["name"] for d in depts]
    assert "Cardiology" in names


def test_admin_add_doctor(client):
    token = login(client)
    resp = client.post("/api/admin/doctors", json={
        "username": "drdoe",
        "email": "drdoe@test.com",
        "password": "doc123",
        "specialization": "Cardiology",
        "phone": "999",
        "qualification": "MBBS",
        "experience_years": 5,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.get_json()["username"] == "drdoe"


def test_admin_list_patients_empty(client):
    token = login(client)
    resp = client.get("/api/admin/patients", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_non_admin_denied(client):
    client.post("/api/auth/register", json={
        "username": "pat1", "email": "pat1@t.com", "password": "p",
        "role": "patient", "phone": "1", "gender": "Male",
        "date_of_birth": "1990-01-01", "blood_group": "A+",
    })
    resp = client.post("/api/auth/login", json={"username": "pat1", "password": "p"})
    token = resp.get_json()["token"]
    resp = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
