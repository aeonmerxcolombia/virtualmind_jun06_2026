import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt_handler import create_access_token

client = TestClient(app)

SUPERADMIN_TOKEN = create_access_token({
    "user_id": "a68acaf2-1610-46d7-a79d-3c57d6a37e65",
    "sub": "isabela@test.com",
    "nombre": "Isabela",
    "roles": ["superadmin"],
    "permissions": [
        "colmena:view_telemetry",
        "colmena:background_task",
        "colmena:admin"
    ]
})

REGISTRADO_TOKEN = create_access_token({
    "user_id": "b78bdbg3-2710-56e8-b89e-4d68e7b48f76",
    "sub": "user@test.com",
    "nombre": "Usuario",
    "roles": ["registrado"],
    "permissions": []
})


@pytest.fixture(autouse=True)
def mock_safety_check():
    with patch('app.colmena.router.ShadowGuardrail.validate_semantic_safety', new_callable=AsyncMock) as m:
        m.return_value = True
        yield


class TestColmena:

    def test_health(self):
        resp = client.get("/colmena/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"
        assert data["version"] == "5.0"

    def test_permissions_endpoint(self):
        resp = client.get("/colmena/permissions")
        assert resp.status_code == 200
        data = resp.json()
        assert "colmena:view_telemetry" in data

    def test_ws_auth_exitoso(self):
        with client.websocket_connect(
            f"/ws/agent/superadmin?token={SUPERADMIN_TOKEN}"
        ) as ws:
            ws.send_text("test")
            data = ws.receive_text()
            assert data is not None

    def test_ws_sin_token_rechazado(self):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/agent/superadmin") as ws:
                ws.receive_text()

    def test_ws_token_invalido_rechazado(self):
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/ws/agent/superadmin?token=token_falso"
            ) as ws:
                ws.receive_text()

    def test_ws_rbac_sin_permiso(self):
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/ws/agent/superadmin?token={REGISTRADO_TOKEN}"
            ) as ws:
                ws.receive_text()

    def test_ws_rol_desconocido(self):
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/ws/agent/rolinexistente?token={SUPERADMIN_TOKEN}"
            ) as ws:
                ws.receive_text()

    def test_ws_comando_query(self):
        with client.websocket_connect(
            f"/ws/agent/superadmin?token={SUPERADMIN_TOKEN}"
        ) as ws:
            ws.send_text("muestra proyectos")
            data = ws.receive_text()
            assert data is not None

    def test_ws_formato_invalido(self):
        with client.websocket_connect(
            f"/ws/agent/superadmin?token={SUPERADMIN_TOKEN}"
        ) as ws:
            ws.send_text("...")
            data = ws.receive_text()
            assert data is not None
