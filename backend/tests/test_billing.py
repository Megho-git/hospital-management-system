def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_invoice_autocreated_on_completion_and_patient_can_view(client):
    # Admin creates doctor
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.get_json()["token"]
    resp = client.post("/api/admin/doctors", json={
        "username": "drbill",
        "email": "drbill@test.com",
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
        "username": "pbill",
        "email": "pbill@test.com",
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
    doc_login = client.post("/api/auth/login", json={"username": "drbill", "password": "doc123"})
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

    # Doctor completes appointment (should auto-create draft invoice)
    resp = client.put(f"/api/doctor/appointments/{apt_id}/complete", json={
        "diagnosis": "ok",
        "prescription": "rest",
        "visit_type": "Routine Checkup",
        "notes": "",
        "medicines": "",
        "prescribed_medicines": [],
    }, headers=_auth(doc_token))
    assert resp.status_code == 200

    # Patient can see invoices list (should contain at least one)
    resp = client.get("/api/patient/invoices", headers=_auth(patient_token))
    assert resp.status_code == 200
    invoices = resp.get_json()
    assert len(invoices) >= 1
    inv = invoices[0]
    assert inv["appointment_id"] == apt_id
    assert inv["status"] == "draft"
    assert inv["items"][0]["item_type"] == "consultation"


def test_admin_mark_invoice_paid(client):
    # admin token
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.get_json()["token"]
    # list invoices (may be empty)
    resp = client.get("/api/admin/invoices", headers=_auth(admin_token))
    assert resp.status_code == 200
    invoices = resp.get_json()
    if not invoices:
        return
    inv = invoices[0]
    resp = client.put(f"/api/admin/invoices/{inv['id']}/pay", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "paid"

