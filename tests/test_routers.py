import pytest


class TestFases:
    def test_list_fases(self, client, test_fase, auth_headers):
        response = client.get("/fases/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_fase(self, client, test_fase, auth_headers):
        response = client.get(f"/fases/{test_fase.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == test_fase.nombre

    def test_get_fase_not_found(self, client, auth_headers):
        response = client.get("/fases/99999", headers=auth_headers)
        assert response.status_code == 404


class TestEtapas:
    def test_list_etapas(self, client, test_etapa, auth_headers):
        response = client.get("/etapas/", headers=auth_headers)
        assert response.status_code == 200

    def test_get_etapa(self, client, test_etapa, auth_headers):
        response = client.get(f"/etapas/{test_etapa.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_get_etapa_not_found(self, client, auth_headers):
        response = client.get("/etapas/99999", headers=auth_headers)
        assert response.status_code == 404


class TestNotifications:
    def test_list_notifications(self, client, test_user, auth_headers):
        response = client.get("/notifications/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_notifications_without_auth(self, client):
        response = client.get("/notifications/")
        assert response.status_code == 401


class TestFolders:
    def test_list_folders(self, client, auth_headers):
        response = client.get("/folders/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestProfile:
    def test_get_profile(self, client, test_user, auth_headers):
        response = client.get(f"/profiles/{test_user.uid}", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_create_or_update_profile(self, client, test_user, auth_headers):
        response = client.post(
            "/profiles/",
            headers=auth_headers,
            json={
                "user_id": test_user.uid,
                "bio": "Bio de prueba",
                "phone": "3001234567",
            },
        )
        assert response.status_code in [200, 201]


class TestModules:
    def test_list_modules(self, client, auth_headers):
        response = client.get("/modules/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_modules_without_auth(self, client):
        response = client.get("/modules/")
        assert response.status_code == 401


class TestAuditLog:
    def test_list_audit_logs(self, client, auth_headers):
        response = client.get("/audit/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_audit_logs_without_auth(self, client):
        response = client.get("/audit/")
        assert response.status_code == 401


class TestConfig:
    def test_get_config(self, client, auth_headers):
        response = client.get("/config/", headers=auth_headers)
        assert response.status_code in [200, 403, 404]


class TestSearch:
    def test_search_global(self, client, auth_headers):
        response = client.get("/search/?q=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)
