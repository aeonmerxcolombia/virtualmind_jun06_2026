import pytest


class TestListRoles:
    def test_list_roles(self, client, test_role, auth_headers):
        response = client.get("/roles/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_roles_without_auth(self, client):
        response = client.get("/roles/")
        assert response.status_code == 401


class TestCreateRole:
    def test_create_role_success(self, client, auth_headers):
        response = client.post(
            "/roles/",
            headers=auth_headers,
            json={"name": "editor", "description": "Editor de contenido"},
        )
        assert response.status_code in [200, 201]

    def test_create_role_duplicate(self, client, test_role, auth_headers):
        response = client.post(
            "/roles/",
            headers=auth_headers,
            json={"name": "superadmin", "description": "Duplicado"},
        )
        assert response.status_code in [400, 409]

    def test_create_role_without_auth(self, client):
        response = client.post(
            "/roles/", json={"name": "noauth", "description": "Sin auth"}
        )
        assert response.status_code == 401


class TestGetRole:
    def test_get_role_by_id(self, client, test_role, auth_headers):
        response = client.get(f"/roles/{test_role.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_role.name

    def test_get_role_not_found(self, client, auth_headers):
        response = client.get("/roles/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateRole:
    def test_update_role(self, client, test_role, auth_headers):
        response = client.put(
            f"/roles/{test_role.id}",
            headers=auth_headers,
            json={"description": "Descripción actualizada"},
        )
        assert response.status_code == 200
        data = response.json() if isinstance(response.json(), dict) else {}
        if data:
            assert data.get("description") == "Descripción actualizada"


class TestDeleteRole:
    def test_delete_role(self, client, test_role_abogado, auth_headers):
        response = client.delete(f"/roles/{test_role_abogado.id}", headers=auth_headers)
        assert response.status_code in [200, 204]

    def test_delete_nonexistent_role(self, client, auth_headers):
        response = client.delete("/roles/99999", headers=auth_headers)
        assert response.status_code == 404


class TestPermissions:
    def test_list_permissions(self, client, test_permission, auth_headers):
        response = client.get("/permissions/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_assign_permission_to_role(
        self, client, test_role, test_permission, auth_headers
    ):
        response = client.post(
            f"/roles/{test_role.id}/permissions",
            headers=auth_headers,
            json={"permission_id": test_permission.id},
        )
        assert response.status_code in [200, 201]

    def test_get_role_permissions(self, client, test_role, auth_headers):
        response = client.get(
            f"/roles/{test_role.id}/permissions", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
