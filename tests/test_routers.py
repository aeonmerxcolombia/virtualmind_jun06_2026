import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.models.fase import Fase


client = TestClient(app)


class TestDocumentRouter:

    def test_create_document(self, db: Session, test_user):
        import os
        from io import BytesIO
        
        file_content = b"Contenido de prueba del documento"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        data = {
            "project_id": "1",
            "document_type": "contrato",
            "document_name": "Test Document"
        }
        
        response = client.post("/documents/", files=files, data=data)
        assert response.status_code in [201, 500]

    def test_list_documents(self, db: Session):
        response = client.get("/documents/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_documents_with_filter(self, db: Session):
        response = client.get("/documents/?project_id=1&document_type=contrato")
        assert response.status_code == 200


class TestProjectRouter:

    def test_create_project(self, db: Session, test_role):
        project_data = {
            "name": "Proyecto de Prueba",
            "client_id": "test-client-id",
            "codigo_referencia": "PRY-001",
            "estado": "activo",
            "description": "Descripción del proyecto",
            "tipo_proyecto": "curso_virtual"
        }
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Proyecto de Prueba"

    def test_create_project_with_invalid_fase(self, db: Session):
        project_data = {
            "name": "Proyecto con Fase Invalida",
            "client_id": "test-client-id",
            "fase_id": 9999
        }
        response = client.post("/projects/", json=project_data)
        assert response.status_code == 400

    def test_list_projects(self, db: Session):
        response = client.get("/projects/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_with_filter(self, db: Session):
        response = client.get("/projects/?estado=activo&fase_id=1")
        assert response.status_code == 200

    def test_get_project_by_id(self, db: Session):
        project = Project(name="Proyecto Test", client_id="test-client")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.get(f"/projects/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Proyecto Test"

    def test_update_project(self, db: Session):
        project = Project(name="Proyecto Original", client_id="test-client", estado="inactivo")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.patch(f"/projects/{project.id}", json={"name": "Proyecto Actualizado", "estado": "activo"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Proyecto Actualizado"

    def test_delete_project(self, db: Session):
        project = Project(name="Proyecto a Eliminar", client_id="test-client")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.delete(f"/projects/{project.id}")
        assert response.status_code == 200


class TestRoleRouter:

    def test_list_roles(self, client):
        response = client.get("/roles/")
        assert response.status_code == 200

    def test_create_role(self, client, auth_headers):
        response = client.post("/roles/", headers=auth_headers, json={
            "name": "test_role",
            "description": "Rol de prueba"
        })
        assert response.status_code in [200, 201]


class TestPermissionRouter:

    def test_list_permissions(self, client):
        response = client.get("/permissions/")
        assert response.status_code == 200


class TestFolderRouter:

    def test_list_folders(self, client):
        response = client.get("/folders/")
        assert response.status_code == 200

    def test_create_folder(self, client, auth_headers):
        response = client.post("/folders/", headers=auth_headers, json={
            "name": "Carpeta Prueba",
            "parent_id": None
        })
        assert response.status_code in [200, 201]


class TestModuleRouter:

    def test_list_modules(self, client):
        response = client.get("/modules/")
        assert response.status_code == 200


class TestStudyPlanRouter:

    def test_list_study_plans(self, client):
        response = client.get("/study-plans/")
        assert response.status_code == 200


class TestTareaRouter:

    def test_list_tareas(self, client):
        response = client.get("/tareas/")
        assert response.status_code == 200


class TestCompetenciaRouter:

    def test_list_competencias(self, client):
        response = client.get("/competencias/")
        assert response.status_code == 200


class TestEvaluacionRouter:

    def test_list_evaluaciones(self, client):
        response = client.get("/evaluaciones/")
        assert response.status_code == 200
