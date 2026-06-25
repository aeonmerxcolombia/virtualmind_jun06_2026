import pytest
from fastapi.testclient import TestClient
from app.auth.hashing import Hash


class TestLogin:
    def test_login_success(self, client, test_user):
        response = client.post(
            "/auth/login",
            json={"username": "test@example.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post(
            "/auth/login",
            json={"username": "test@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/auth/login",
            json={"username": "noexiste@test.com", "password": "testpass123"},
        )
        assert response.status_code == 401

    def test_login_inactive_user(self, client, db, test_role):
        from app.models.user import User

        user = User(
            uid="test-uid-inactive",
            nombre="Inactive User",
            tipo_documento="CC",
            documento="999999999",
            email="inactive@test.com",
            password=Hash.encrypt("testpass123"),
            estado=False,
        )
        user.roles.append(test_role)
        db.add(user)
        db.commit()
        response = client.post(
            "/auth/login",
            json={"username": "inactive@test.com", "password": "testpass123"},
        )
        assert response.status_code == 401

    def test_login_empty_email(self, client):
        response = client.post(
            "/auth/login", json={"username": "", "password": "testpass123"}
        )
        assert response.status_code in [401, 422]


class TestRegister:
    def test_register_success(self, client, db, test_role):
        response = client.post(
            "/auth/register",
            json={
                "nombre": "Nuevo Usuario",
                "email": "nuevo@test.com",
                "password": "SecurePass1!",
                "tipo_documento": "CC",
                "documento": "555666777",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["email"] == "nuevo@test.com"

    def test_register_existing_email(self, client, test_user):
        response = client.post(
            "/auth/register",
            json={
                "nombre": "Duplicado",
                "email": "test@example.com",
                "password": "SecurePass1!",
                "tipo_documento": "CC",
                "documento": "111222333",
            },
        )
        assert response.status_code == 400

    def test_register_weak_password(self, client):
        response = client.post(
            "/auth/register",
            json={
                "nombre": "Weak Password",
                "email": "weak@test.com",
                "password": "123",
                "tipo_documento": "CC",
                "documento": "000000001",
            },
        )
        assert response.status_code in [400, 422]


class TestProfile:
    def test_get_profile_authenticated(self, client, auth_headers, test_user):
        response = client.get("/auth/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    def test_get_profile_unauthenticated(self, client):
        response = client.get("/auth/profile")
        assert response.status_code == 401

    def test_update_profile(self, client, auth_headers):
        response = client.put(
            "/auth/profile", headers=auth_headers, json={"nombre": "Nombre Actualizado"}
        )
        assert response.status_code in [200, 201]
        data = response.json() if response.status_code == 200 else {}
        if data:
            assert data.get("nombre") == "Nombre Actualizado"


class TestCheckEmail:
    def test_check_email_exists(self, client, test_user):
        response = client.get("/auth/check-email", params={"email": "test@example.com"})
        assert response.status_code == 200
        assert response.json()["existe"] is True

    def test_check_email_not_exists(self, client):
        response = client.get(
            "/auth/check-email", params={"email": "noexiste@test.com"}
        )
        assert response.status_code == 200
        assert response.json()["existe"] is False
