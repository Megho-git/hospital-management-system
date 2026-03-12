def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_doctor_can_record_and_fetch_vitals(client):
    # Create doctor via admin
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.get_json()["token"]
    resp = client.post("/api/admin/doctors", json={
        "username": "drvital",
        "email": "drvital@test.com",
        "password": "doc123",
        "specialization": "General",
        "phone": "999",
        "qualification": "MBBS",
        "experience_years": 2,
    }, headers=_auth(admin_token))
    assert resp.status_code == 201
    doctor_id = resp.get_json()["id"]

    # Register patient + book appointment with this doctor
    reg = client.post("/api/auth/register", json={
        "username": "pvital",
        "email": "pvital@test.com",
        "password": "test123",
        "role": "patient",
        "phone": "123456",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "blood_group": "O+",
    })
    assert reg.status_code == 201
    patient_token = reg.get_json()["token"]

    # Create availability for the doctor by logging in as doctor
    doc_login = client.post("/api/auth/login", json={"username": "drvital", "password": "doc123"})
    assert doc_login.status_code == 200
    doc_token = doc_login.get_json()["token"]

    from datetime import date, timedelta
    d = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post("/api/doctor/availability", json={
        "slots": [{"date": d, "start_time": "10:00", "end_time": "11:00"}]
    }, headers=_auth(doc_token))
    assert resp.status_code == 200

    # Patient books appointment
    resp = client.post("/api/patient/appointments", json={
        "doctor_id": doctor_id,
        "date": d,
        "time_slot": "10:00",
        "reason": "checkup",
    }, headers=_auth(patient_token))
    assert resp.status_code == 201
    apt_id = resp.get_json()["id"]

    # Doctor records vitals
    resp = client.post(f"/api/doctor/appointments/{apt_id}/vitals", json={
        "temperature": 37.2,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "pulse_rate": 72,
        "spo2": 98,
        "respiratory_rate": 16,
        "notes": "stable",
    }, headers=_auth(doc_token))
    assert resp.status_code == 201
    v = resp.get_json()
    assert v["appointment_id"] == apt_id
    assert v["pulse_rate"] == 72

    # Doctor fetches vitals
    resp = client.get(f"/api/doctor/appointments/{apt_id}/vitals", headers=_auth(doc_token))
    assert resp.status_code == 200
    v = resp.get_json()
    assert v["spo2"] == 98


def test_patient_can_view_vitals_history(client):
    reg = client.post("/api/auth/register", json={
        "username": "pvital2",
        "email": "pvital2@test.com",
        "password": "test123",
        "role": "patient",
        "phone": "123456",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "blood_group": "O+",
    })
    assert reg.status_code == 201
    token = reg.get_json()["token"]
    resp = client.get("/api/patient/vitals", headers=_auth(token))
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

