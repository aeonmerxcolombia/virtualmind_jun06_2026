import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app


client = TestClient(app)


class TestAuthRouter:

    def test_register_user_success(self, db: Session, test_role):
        response = client.post("/auth/register", json={
            "nombre": "Nuevo Usuario",
            "email": "nuevo@test.com",
            "password": "password123",
            "tipo_documento": "CC",
            "documento": "987654321",
            "role_ids": [test_role.id]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["msg"] == "Usuario creado exitosamente"
        assert "uid" in data

    def test_register_user_email_exists(self, db: Session, test_user, test_role):
        response = client.post("/auth/register", json={
            "nombre": "Nuevo Usuario",
            "email": test_user.email,
            "password": "password123",
            "tipo_documento": "CC",
            "documento": "987654321",
            "role_ids": [test_role.id]
        })
        assert response.status_code == 400
        assert "ya registrado" in response.json()["detail"]

    def test_register_user_invalid_role(self, db: Session):
        response = client.post("/auth/register", json={
            "nombre": "Nuevo Usuario",
            "email": "nuevo@test.com",
            "password": "password123",
            "tipo_documento": "CC",
            "documento": "987654321",
            "role_ids": [999]
        })
        assert response.status_code == 400
        assert "role_id" in response.json()["detail"]

    def test_check_email_exists_true(self, db: Session, test_user):
        response = client.get(f"/users/check-email?email={test_user.email}")
        assert response.status_code == 200
        assert response.json()["existe"] is True

    def test_check_email_exists_false(self, db: Session):
        response = client.get("/users/check-email?email=noexiste@test.com")
        assert response.status_code == 200
        assert response.json()["existe"] is False


class TestChatRouter:

    def test_chat_ollama(self):
        with patch("app.routes.chat.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                raise_for_status=MagicMock(),
                json=lambda: {"response": "Hola desde Ollama"}
            )
            response = client.post("/chat/ollama", json={
                "prompt": "Hola",
                "model": "llama3.2"
            })
            assert response.status_code == 200
            data = response.json()
            assert "respuesta" in data

    def test_chat_gemini(self):
        with patch("app.routes.chat.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                raise_for_status=MagicMock(),
                json=lambda: {"candidates": [{"content": {"parts": [{"text": "Respuesta Gemini"}]}}]}
            )
            response = client.post("/chat/gemini", json={
                "prompt": "Hola"
            })
            assert response.status_code == 200

    def test_generar_contenido(self):
        with patch("app.routes.chat.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                raise_for_status=MagicMock(),
                json=lambda: {"candidates": [{"content": {"parts": [{"text": "Contenido generado"}]}}]}
            )
            response = client.post("/chat/generar-contenido", json={
                "prompt": "Genera un resumen"
            })
            assert response.status_code == 200
