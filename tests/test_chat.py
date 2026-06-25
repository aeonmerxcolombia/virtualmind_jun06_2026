import pytest


class TestChatMessages:
    def test_get_chat_messages(self, client, auth_headers):
        response = client.get("/chat/messages", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_chat_messages_without_auth(self, client):
        response = client.get("/chat/messages")
        assert response.status_code == 401

    def test_send_message_without_auth(self, client):
        response = client.post(
            "/chat/messages", json={"content": "Hola", "receiver_id": "test-uid"}
        )
        assert response.status_code == 401


class TestChatConversations:
    def test_list_conversations(self, client, auth_headers):
        response = client.get("/chat/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_conversations_without_auth(self, client):
        response = client.get("/chat/conversations")
        assert response.status_code == 401


class TestMensajes:
    def test_list_mensajes(self, client, auth_headers):
        response = client.get("/mensajes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_mensajes_without_auth(self, client):
        response = client.get("/mensajes/")
        assert response.status_code == 401
