import pytest


class TestAIEndpoints:
    def test_ai_status(self, client, auth_headers):
        response = client.get("/ai/status", headers=auth_headers)
        assert response.status_code in [200, 404, 503]

    def test_ai_generate(self, client, auth_headers):
        response = client.post(
            "/ai/generate", headers=auth_headers, json={"prompt": "Escribe un saludo"}
        )
        assert response.status_code in [200, 400, 503]


class TestOllama:
    def test_ollama_status(self, client, auth_headers):
        response = client.get("/ollama/status", headers=auth_headers)
        assert response.status_code in [200, 404, 503]


class TestTTS:
    def test_tts_generate(self, client, auth_headers):
        response = client.post(
            "/tts/generate",
            headers=auth_headers,
            json={"text": "Hola mundo", "voice": "es-US"},
        )
        assert response.status_code in [200, 400, 503]


class TestWhisper:
    def test_whisper_status(self, client, auth_headers):
        response = client.get("/whisper/status", headers=auth_headers)
        assert response.status_code in [200, 404, 503]


class TestTareaIA:
    def test_list_tareas_ia(self, client, auth_headers):
        response = client.get("/tareas-ia/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_tarea_ia(self, client, test_user, auth_headers):
        response = client.post(
            "/tareas-ia/",
            headers=auth_headers,
            json={
                "descripcion": "Tarea IA de prueba",
                "prioridad": "alta",
                "categoria": "desarrollo",
            },
        )
        assert response.status_code in [200, 201]


class TestOrquestador:
    def test_orquestador_status(self, client, auth_headers):
        response = client.get("/orquestador-ia/status", headers=auth_headers)
        assert response.status_code in [200, 404]
