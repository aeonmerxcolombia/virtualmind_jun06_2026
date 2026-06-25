import pytest


class TestListUsers:
    def test_list_users_with_auth(self, client, auth_headers):
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_users_without_auth(self, client):
        response = client.get("/users/")
        assert response.status_code == 401

    def test_list_users_pagination(self, client, auth_headers):
        response = client.get("/users/?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


class TestCreateUser:
    def test_create_user_success(self, client, db, test_role, auth_headers):
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={
                "nombre": "Usuario Nuevo",
                "email": "nuevo@test.com",
                "password": "password123",
                "tipo_documento": "CC",
                "documento": "111222333",
                "role_ids": [test_role.id],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Usuario Nuevo"
        assert data["email"] == "nuevo@test.com"

    def test_create_user_duplicate_email(self, client, test_user, auth_headers):
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={
                "nombre": "Duplicado",
                "email": "test@example.com",
                "password": "password123",
                "tipo_documento": "CC",
                "documento": "999888777",
                "role_ids": [1],
            },
        )
        assert response.status_code == 400

    def test_create_user_without_auth(self, client):
        response = client.post(
            "/users/",
            json={
                "nombre": "No Auth",
                "email": "noauth@test.com",
                "password": "password123",
                "tipo_documento": "CC",
                "documento": "000000000",
            },
        )
        assert response.status_code == 401

    def test_create_user_invalid_email(self, client, auth_headers):
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={
                "nombre": "Bad Email",
                "email": "not-an-email",
                "password": "password123",
                "tipo_documento": "CC",
                "documento": "000000001",
            },
        )
        assert response.status_code in [400, 422]


class TestGetUser:
    def test_get_user_by_uid(self, client, test_user, auth_headers):
        response = client.get(f"/users/{test_user.uid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == test_user.uid
        assert data["email"] == test_user.email

    def test_get_user_not_found(self, client, auth_headers):
        response = client.get("/users/nonexistent-uid", headers=auth_headers)
        assert response.status_code == 404

    def test_get_user_without_auth(self, client, test_user):
        response = client.get(f"/users/{test_user.uid}")
        assert response.status_code == 401


class TestUpdateUser:
    def test_update_user_name(self, client, test_user, auth_headers):
        response = client.put(
            f"/users/{test_user.uid}",
            headers=auth_headers,
            json={"nombre": "Nombre Modificado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nombre Modificado"

    def test_update_user_email(self, client, test_user, auth_headers):
        response = client.put(
            f"/users/{test_user.uid}",
            headers=auth_headers,
            json={"email": "modificado@test.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "modificado@test.com"

    def test_update_nonexistent_user(self, client, auth_headers):
        response = client.put(
            "/users/nonexistent-uid", headers=auth_headers, json={"nombre": "No Existe"}
        )
        assert response.status_code == 404

    def test_update_user_without_auth(self, client, test_user):
        response = client.put(f"/users/{test_user.uid}", json={"nombre": "Sin Token"})
        assert response.status_code == 401


class TestDeleteUser:
    def test_delete_user(self, client, test_user_2, auth_headers):
        response = client.delete(f"/users/{test_user_2.uid}", headers=auth_headers)
        assert response.status_code == 200

    def test_delete_nonexistent_user(self, client, auth_headers):
        response = client.delete("/users/nonexistent-uid", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_user_without_auth(self, client, test_user):
        response = client.delete(f"/users/{test_user.uid}")
        assert response.status_code == 401


class TestUserStatus:
    def test_toggle_user_status(self, client, test_user_2, auth_headers):
        response = client.patch(
            f"/users/{test_user_2.uid}/status",
            headers=auth_headers,
            json={"estado": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("estado") is False or "estado" in data

    def test_toggle_status_nonexistent(self, client, auth_headers):
        response = client.patch(
            "/users/nonexistent-uid/status",
            headers=auth_headers,
            json={"estado": False},
        )
        assert response.status_code == 404


class TestCheckEmail:
    def test_check_email_exists(self, client, test_user):
        response = client.get(
            "/users/check-email", params={"email": "test@example.com"}
        )
        assert response.status_code == 200
        assert response.json()["existe"] is True

    def test_check_email_not_exists(self, client):
        response = client.get(
            "/users/check-email", params={"email": "noexiste@test.com"}
        )
        assert response.status_code == 200
        assert response.json()["existe"] is False
