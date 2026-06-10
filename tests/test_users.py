import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.role import Role
from app.auth.jwt_handler import createJWT


client = TestClient(app)


class TestUsersRouter:

    def test_list_users_with_auth(self, client, test_user, auth_headers):
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_users_without_auth(self, client):
        response = client.get("/users/")
        assert response.status_code == 401

    def test_get_user_by_uid(self, client, test_user, auth_headers):
        response = client.get(f"/users/{test_user.uid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == test_user.uid
        assert data["email"] == test_user.email

    def test_get_user_not_found(self, client, auth_headers):
        response = client.get("/users/uid-inexistente", headers=auth_headers)
        assert response.status_code == 404

    def test_create_user(self, client, db, test_role, auth_headers):
        response = client.post("/users/", headers=auth_headers, json={
            "nombre": "Usuario Prueba",
            "email": "prueba@test.com",
            "password": "password123",
            "tipo_documento": "CC",
            "documento": "111222333",
            "role_ids": [test_role.id]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Usuario Prueba"
        assert data["email"] == "prueba@test.com"

    def test_create_user_email_exists(self, client, test_user, auth_headers):
        response = client.post("/users/", headers=auth_headers, json={
            "nombre": "Usuario Duplicate",
            "email": test_user.email,
            "password": "password123",
            "tipo_documento": "CC",
            "documento": "111222333",
            "role_ids": []
        })
        assert response.status_code == 400

    def test_update_user(self, client, test_user, auth_headers):
        response = client.patch(f"/users/{test_user.uid}", headers=auth_headers, json={
            "nombre": "Nombre Actualizado"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nombre Actualizado"

    def test_update_user_email(self, client, test_user, auth_headers):
        response = client.patch(f"/users/{test_user.uid}/email", headers=auth_headers, json={
            "email": "nuevoemail@test.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "nuevoemail@test.com"

    def test_deactivate_user(self, client, test_user, auth_headers):
        response = client.delete(f"/users/{test_user.uid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["msg"] == "Usuario desactivado"

    def test_delete_user_hard(self, client, test_user, auth_headers):
        response = client.delete(f"/users/hard/{test_user.uid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "eliminado permanentemente" in data["msg"]

    def test_get_user_permissions(self, client, test_user, auth_headers):
        response = client.get(f"/users/{test_user.uid}/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "uid" in data
        assert "roles" in data
        assert "permissions" in data


class TestAcceptTerms:

    def test_accept_terms_success(self, client, test_user, auth_headers):
        response = client.put("/users/me/accept-terms", headers=auth_headers)
        assert response.status_code == 204

    def test_accept_terms_without_auth(self, client):
        response = client.put("/users/me/accept-terms")
        assert response.status_code == 401
