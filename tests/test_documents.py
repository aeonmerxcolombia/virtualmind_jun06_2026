import pytest
from io import BytesIO


class TestCreateDocument:
    def test_create_document_success(self, client, test_project, auth_headers):
        file_content = b"Contenido del documento de prueba"
        response = client.post(
            "/documents/",
            headers=auth_headers,
            files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
            data={
                "project_id": str(test_project.id),
                "document_type": "contrato",
                "document_name": "Documento Test",
            },
        )
        assert response.status_code in [200, 201]

    def test_create_document_without_file(self, client, test_project, auth_headers):
        response = client.post(
            "/documents/",
            headers=auth_headers,
            data={
                "project_id": str(test_project.id),
                "document_type": "contrato",
                "document_name": "Sin Archivo",
            },
        )
        assert response.status_code in [400, 422]

    def test_create_document_without_auth(self, client, test_project):
        response = client.post(
            "/documents/",
            files={"file": ("test.txt", BytesIO(b"test"), "text/plain")},
            data={"project_id": str(test_project.id), "document_type": "contrato"},
        )
        assert response.status_code == 401


class TestListDocuments:
    def test_list_documents(self, client, auth_headers):
        response = client.get("/documents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_documents_filter_by_project(self, client, test_project, auth_headers):
        response = client.get(
            f"/documents/?project_id={test_project.id}", headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_documents_without_auth(self, client):
        response = client.get("/documents/")
        assert response.status_code == 401


class TestGetDocument:
    def test_get_document_not_found(self, client, auth_headers):
        response = client.get("/documents/99999", headers=auth_headers)
        assert response.status_code == 404


class TestDeleteDocument:
    def test_delete_document_not_found(self, client, auth_headers):
        response = client.delete("/documents/99999", headers=auth_headers)
        assert response.status_code == 404
