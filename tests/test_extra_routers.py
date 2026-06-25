import pytest


class TestCronograma:
    def test_list_cronogramas(self, client, auth_headers):
        response = client.get("/cronogramas/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_cronogramas_without_auth(self, client):
        response = client.get("/cronogramas/")
        assert response.status_code == 401


class TestBitacora:
    def test_list_bitacora(self, client, auth_headers):
        response = client.get("/bitacora/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestContact:
    def test_create_contact_message(self, client, auth_headers):
        response = client.post(
            "/contact/",
            headers=auth_headers,
            json={
                "nombre": "Contacto Test",
                "email": "contacto@test.com",
                "mensaje": "Mensaje de prueba",
            },
        )
        assert response.status_code in [200, 201]


class TestResources:
    def test_list_resources(self, client, auth_headers):
        response = client.get("/resources/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_resources_without_auth(self, client):
        response = client.get("/resources/")
        assert response.status_code == 401


class TestEvents:
    def test_list_events(self, client, auth_headers):
        response = client.get("/events/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestArchivos:
    def test_list_archivos(self, client, auth_headers):
        response = client.get("/archivos/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestEvaluaciones:
    def test_list_evaluaciones(self, client, auth_headers):
        response = client.get("/evaluaciones/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUnits:
    def test_list_units(self, client, auth_headers):
        response = client.get("/units/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestLearningActivities:
    def test_list_activities(self, client, auth_headers):
        response = client.get("/learning-activities/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
