import pytest


class TestCreateClient:
    def test_create_client_success(self, client, auth_headers):
        response = client.post(
            "/clients/",
            headers=auth_headers,
            json={
                "nombre": "Cliente Test",
                "email": "cliente@test.com",
                "telefono": "3001234567",
                "tipo_documento": "NIT",
                "documento": "900123456",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json() if isinstance(response.json(), dict) else {}
        if data:
            assert data.get("nombre") == "Cliente Test"

    def test_create_client_without_auth(self, client):
        response = client.post(
            "/clients/", json={"nombre": "Sin Auth", "email": "noauth@test.com"}
        )
        assert response.status_code == 401


class TestListClients:
    def test_list_clients(self, client, auth_headers):
        response = client.get("/clients/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_clients_without_auth(self, client):
        response = client.get("/clients/")
        assert response.status_code == 401


class TestGetClient:
    def test_get_client_not_found(self, client, auth_headers):
        response = client.get("/clients/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateClient:
    def test_update_client_not_found(self, client, auth_headers):
        response = client.put(
            "/clients/99999", headers=auth_headers, json={"nombre": "No Existe"}
        )
        assert response.status_code == 404
