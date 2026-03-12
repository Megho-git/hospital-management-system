def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_refresh_token_endpoint(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "refresh_token" in data
    refresh = data["refresh_token"]

    resp = client.post("/api/auth/refresh", headers=_auth(refresh))
    assert resp.status_code == 200
    assert "token" in resp.get_json()


def test_notifications_created_and_listed(client):
    # Admin creates doctor
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.get_json()["token"]
    resp = client.post("/api/admin/doctors", json={
        "username": "drnotif",
        "email": "drnotif@test.com",
        "password": "doc123",
        "specialization": "General",
        "phone": "999",
        "qualification": "MBBS",
        "experience_years": 2,
    }, headers=_auth(admin_token))
    assert resp.status_code == 201
    doctor_id = resp.get_json()["id"]

    # Doctor login
    doc_login = client.post("/api/auth/login", json={"username": "drnotif", "password": "doc123"})
    doc_token = doc_login.get_json()["token"]

    # Register patient
    reg = client.post("/api/auth/register", json={
        "username": "pnotif",
        "email": "pnotif@test.com",
        "password": "test1234",
        "role": "patient",
        "phone": "123456",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "blood_group": "O+",
    })
    assert reg.status_code == 201
    patient_token = reg.get_json()["token"]

    # Availability
    from datetime import date, timedelta
    d = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post("/api/doctor/availability", json={
        "slots": [{"date": d, "start_time": "10:00", "end_time": "11:00"}]
    }, headers=_auth(doc_token))
    assert resp.status_code == 200

    # Patient books -> creates notification to doctor
    resp = client.post("/api/patient/appointments", json={
        "doctor_id": doctor_id,
        "date": d,
        "time_slot": "10:00",
        "reason": "checkup",
    }, headers=_auth(patient_token))
    assert resp.status_code == 201

    # Doctor lists notifications
    resp = client.get("/api/notifications/", headers=_auth(doc_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert any(n["type"] == "appointment" for n in data["items"])

