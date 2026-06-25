import pytest


class TestPasswordRecovery:
    def test_request_recovery_nonexistent(self, client):
        response = client.post("/auth/recovery", json={"email": "noexiste@test.com"})
        assert response.status_code in [200, 404]

    def test_request_recovery_existing(self, client, test_user):
        response = client.post("/auth/recovery", json={"email": test_user.email})
        assert response.status_code == 200


class TestSwitchRole:
    def test_switch_role_valid(self, client, test_user, test_role, auth_headers):
        response = client.post(
            "/auth/switch-role", headers=auth_headers, json={"role": "superadmin"}
        )
        assert response.status_code in [200, 400]

    def test_switch_role_invalid(self, client, auth_headers):
        response = client.post(
            "/auth/switch-role", headers=auth_headers, json={"role": "rol_inexistente"}
        )
        assert response.status_code in [400, 404]

    def test_switch_role_without_auth(self, client):
        response = client.post("/auth/switch-role", json={"role": "superadmin"})
        assert response.status_code == 401


class Test2FA:
    def test_request_2fa_code(self, client):
        response = client.post("/auth/2fa/request", json={"email": "test@example.com"})
        assert response.status_code in [200, 400, 429]

    def test_verify_2fa_invalid_code(self, client):
        response = client.post(
            "/auth/2fa/verify", json={"email": "test@example.com", "code": "000000"}
        )
        assert response.status_code in [400, 401]

    def test_verify_2fa_without_email(self, client):
        response = client.post("/auth/2fa/verify", json={"email": "", "code": "123456"})
        assert response.status_code in [400, 422]
