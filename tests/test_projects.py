import pytest


class TestCreateProject:
    def test_create_project_success(self, client, test_user, auth_headers):
        response = client.post(
            "/projects/",
            headers=auth_headers,
            json={
                "name": "Nuevo Proyecto",
                "client_id": test_user.uid,
                "codigo_referencia": "PRY-002",
                "estado": "activo",
                "description": "Descripción del proyecto",
                "tipo_proyecto": "curso_virtual",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json() if response.status_code == 200 else {}
        if data:
            assert data["name"] == "Nuevo Proyecto"
            assert data["codigo_referencia"] == "PRY-002"

    def test_create_project_without_auth(self, client, test_user):
        response = client.post(
            "/projects/",
            json={
                "name": "Sin Auth",
                "client_id": test_user.uid,
                "codigo_referencia": "PRY-003",
                "estado": "activo",
                "tipo_proyecto": "curso_virtual",
            },
        )
        assert response.status_code == 401

    def test_create_project_missing_required(self, client, auth_headers):
        response = client.post(
            "/projects/", headers=auth_headers, json={"name": "Incompleto"}
        )
        assert response.status_code in [400, 422]


class TestListProjects:
    def test_list_projects(self, client, test_project, auth_headers):
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_projects_without_auth(self, client):
        response = client.get("/projects/")
        assert response.status_code == 401

    def test_list_projects_filter_by_status(self, client, test_project, auth_headers):
        response = client.get("/projects/?estado=activo", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_filter_invalid_status(self, client, auth_headers):
        response = client.get("/projects/?estado=inexistente", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGetProject:
    def test_get_project_by_id(self, client, test_project, auth_headers):
        response = client.get(f"/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_project.name
        assert data["codigo_referencia"] == test_project.codigo_referencia

    def test_get_project_not_found(self, client, auth_headers):
        response = client.get("/projects/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_project_without_auth(self, client, test_project):
        response = client.get(f"/projects/{test_project.id}")
        assert response.status_code == 401


class TestUpdateProject:
    def test_update_project_name(self, client, test_project, auth_headers):
        response = client.put(
            f"/projects/{test_project.id}",
            headers=auth_headers,
            json={"name": "Proyecto Modificado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Proyecto Modificado"

    def test_update_project_status(self, client, test_project, auth_headers):
        response = client.put(
            f"/projects/{test_project.id}",
            headers=auth_headers,
            json={"estado": "completado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "completado"

    def test_update_nonexistent_project(self, client, auth_headers):
        response = client.put(
            "/projects/99999", headers=auth_headers, json={"name": "No Existe"}
        )
        assert response.status_code == 404


class TestDeleteProject:
    def test_delete_project(self, client, test_project, auth_headers):
        response = client.delete(f"/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code in [200, 204]

    def test_delete_nonexistent_project(self, client, auth_headers):
        response = client.delete("/projects/99999", headers=auth_headers)
        assert response.status_code == 404


class TestProjectPhases:
    def test_list_project_phases(self, client, test_project, test_fase, auth_headers):
        response = client.get(
            f"/projects/{test_project.id}/fases", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_phase_to_project(self, client, test_project, auth_headers):
        response = client.post(
            f"/projects/{test_project.id}/fases",
            headers=auth_headers,
            json={"nombre": "Nueva Fase", "orden": 2},
        )
        assert response.status_code in [200, 201]
