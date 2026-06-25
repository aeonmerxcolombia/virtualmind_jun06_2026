import pytest


class TestCreateTarea:
    def test_create_tarea_success(self, client, test_etapa, test_user, auth_headers):
        response = client.post(
            "/tareas/",
            headers=auth_headers,
            json={
                "titulo": "Nueva Tarea",
                "descripcion": "Descripción de la tarea",
                "etapa_id": test_etapa.id,
                "asignado_a": test_user.uid,
                "estado": "pendiente",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json() if isinstance(response.json(), dict) else {}
        if data:
            assert data.get("titulo") == "Nueva Tarea"

    def test_create_tarea_without_auth(self, client, test_etapa):
        response = client.post(
            "/tareas/", json={"titulo": "Sin Auth", "etapa_id": test_etapa.id}
        )
        assert response.status_code == 401

    def test_create_tarea_invalid_etapa(self, client, auth_headers):
        response = client.post(
            "/tareas/",
            headers=auth_headers,
            json={
                "titulo": "Etapa Invalida",
                "etapa_id": 99999,
                "asignado_a": "test-uid",
            },
        )
        assert response.status_code in [400, 404]


class TestListTareas:
    def test_list_tareas(self, client, test_tarea, auth_headers):
        response = client.get("/tareas/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tareas_filter_by_estado(self, client, test_tarea, auth_headers):
        response = client.get("/tareas/?estado=pendiente", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tareas_filter_by_asignado(
        self, client, test_tarea, test_user, auth_headers
    ):
        response = client.get(
            f"/tareas/?asignado_a={test_user.uid}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tareas_without_auth(self, client):
        response = client.get("/tareas/")
        assert response.status_code == 401


class TestGetTarea:
    def test_get_tarea_by_id(self, client, test_tarea, auth_headers):
        response = client.get(f"/tareas/{test_tarea.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["titulo"] == test_tarea.titulo

    def test_get_tarea_not_found(self, client, auth_headers):
        response = client.get("/tareas/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateTarea:
    def test_update_tarea_status(self, client, test_tarea, auth_headers):
        response = client.patch(
            f"/tareas/{test_tarea.id}/status",
            headers=auth_headers,
            json={"estado": "en_progreso"},
        )
        assert response.status_code == 200
        if isinstance(response.json(), dict):
            assert response.json().get("estado") == "en_progreso"

    def test_update_tarea(self, client, test_tarea, auth_headers):
        response = client.put(
            f"/tareas/{test_tarea.id}",
            headers=auth_headers,
            json={"titulo": "Tarea Actualizada"},
        )
        assert response.status_code in [200, 201]
        if isinstance(response.json(), dict):
            assert response.json().get("titulo") == "Tarea Actualizada"

    def test_update_nonexistent_tarea(self, client, auth_headers):
        response = client.put(
            "/tareas/99999", headers=auth_headers, json={"titulo": "No Existe"}
        )
        assert response.status_code == 404


class TestDeleteTarea:
    def test_delete_tarea(self, client, test_tarea, auth_headers):
        response = client.delete(f"/tareas/{test_tarea.id}", headers=auth_headers)
        assert response.status_code in [200, 204]

    def test_delete_nonexistent_tarea(self, client, auth_headers):
        response = client.delete("/tareas/99999", headers=auth_headers)
        assert response.status_code == 404
