def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_lab_order_flow_end_to_end(client):
    # Admin token
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.get_json()["token"]

    # Create lab test
    resp = client.post("/api/admin/lab-tests", json={
        "name": "Fasting Glucose",
        "category": "Biochemistry",
        "unit": "mg/dL",
        "normal_range": "70-110",
        "description": "Blood glucose after fasting",
        "is_active": True,
    }, headers=_auth(admin_token))
    assert resp.status_code == 201
    lab_test_id = resp.get_json()["id"]

    # Create doctor
    resp = client.post("/api/admin/doctors", json={
        "username": "drlab",
        "email": "drlab@test.com",
        "password": "doc123",
        "specialization": "General",
        "phone": "999",
        "qualification": "MBBS",
        "experience_years": 2,
    }, headers=_auth(admin_token))
    assert resp.status_code == 201
    doctor_id = resp.get_json()["id"]

    # Register patient
    reg = client.post("/api/auth/register", json={
        "username": "plab",
        "email": "plab@test.com",
        "password": "test123",
        "role": "patient",
        "phone": "123456",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "blood_group": "O+",
    })
    assert reg.status_code == 201
    patient_token = reg.get_json()["token"]

    # Doctor login + availability
    doc_login = client.post("/api/auth/login", json={"username": "drlab", "password": "doc123"})
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

    # Doctor orders lab test
    resp = client.post(f"/api/doctor/appointments/{apt_id}/lab-orders", json={
        "lab_test_ids": [lab_test_id],
    }, headers=_auth(doc_token))
    assert resp.status_code == 201
    created = resp.get_json()
    assert len(created) == 1
    order_id = created[0]["id"]
    assert created[0]["lab_test"]["name"] == "Fasting Glucose"

    # Doctor updates result
    resp = client.put(f"/api/doctor/lab-orders/{order_id}", json={
        "status": "resulted",
        "result_value": "140",
        "result_notes": "Elevated",
    }, headers=_auth(doc_token))
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["status"] == "resulted"
    assert updated["result_value"] == "140"

    # Patient can see lab result
    resp = client.get("/api/patient/lab-results", headers=_auth(patient_token))
    assert resp.status_code == 200
    results = resp.get_json()
    assert len(results) >= 1
    assert results[0]["lab_test"]["name"] == "Fasting Glucose"

    # Summary includes lab_orders
    resp = client.get(f"/api/patient/appointments/{apt_id}/summary", headers=_auth(patient_token))
    assert resp.status_code == 200
    summary = resp.get_json()
    assert "lab_orders" in summary
    assert summary["lab_orders"][0]["result_value"] == "140"

