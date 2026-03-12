def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_fetch_audit_log(client):
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200
    token = admin_login.get_json()["token"]

    resp = client.get("/api/admin/audit-log", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert "total" in data

