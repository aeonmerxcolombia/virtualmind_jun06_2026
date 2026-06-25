import pytest


class TestBiblioteca:
    def test_list_biblioteca(self, client, auth_headers):
        response = client.get("/biblioteca/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_biblioteca_without_auth(self, client):
        response = client.get("/biblioteca/")
        assert response.status_code == 401

    def test_get_biblioteca_item_not_found(self, client, auth_headers):
        response = client.get("/biblioteca/99999", headers=auth_headers)
        assert response.status_code == 404


class TestRRHH:
    def test_list_rrhh(self, client, auth_headers):
        response = client.get("/rrhh/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_rrhh_without_auth(self, client):
        response = client.get("/rrhh/")
        assert response.status_code == 401


class TestCompetencias:
    def test_list_competencias(self, client, auth_headers):
        response = client.get("/competencias/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_competencia(self, client, auth_headers):
        response = client.post(
            "/competencias/",
            headers=auth_headers,
            json={"nombre": "Competencia Test", "descripcion": "Descripción"},
        )
        assert response.status_code in [200, 201]


class TestSolicitudes:
    def test_list_solicitudes(self, client, auth_headers):
        response = client.get("/solicitudes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_solicitud(self, client, test_user, auth_headers):
        response = client.post(
            "/solicitudes/",
            headers=auth_headers,
            json={
                "tipo": "acceso",
                "descripcion": "Solicitud de prueba",
                "usuario_id": test_user.uid,
            },
        )
        assert response.status_code in [200, 201]


class TestVencimientos:
    def test_list_vencimientos(self, client, auth_headers):
        response = client.get("/vencimientos/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
