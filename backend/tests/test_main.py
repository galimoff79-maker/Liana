"""
Backend tests for ПриватЧат
"""
import pytest

# ============ Auth Tests ============

class TestRegistration:
    def test_register_first_user(self, client):
        response = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "invite_code" in data
        assert data["user"]["username"] == "user1"

    def test_register_second_user_with_invite(self, client):
        # Register first user
        reg = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        invite_code = reg.json()["invite_code"]
        
        # Register second user
        response = client.post("/api/auth/register-with-invite", json={
            "username": "user2",
            "password": "password456",
            "display_name": "User Two",
            "invite_code": invite_code
        })
        assert response.status_code == 200
        assert "token" in response.json()

    def test_register_third_user_blocked(self, client):
        # Register two users
        reg1 = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        client.post("/api/auth/register-with-invite", json={
            "username": "user2",
            "password": "password456",
            "display_name": "User Two",
            "invite_code": reg1.json()["invite_code"]
        })
        
        # Try to register third user
        response = client.post("/api/auth/register", json={
            "username": "user3",
            "password": "password789",
            "display_name": "User Three"
        })
        assert response.status_code == 403

    def test_register_duplicate_username(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password456",
            "display_name": "Another User"
        })
        assert response.status_code == 400

    def test_register_short_password(self, client):
        response = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "12345",
            "display_name": "User One"
        })
        assert response.status_code == 400

    def test_register_short_username(self, client):
        response = client.post("/api/auth/register", json={
            "username": "ab",
            "password": "password123",
            "display_name": "User One"
        })
        assert response.status_code == 400

    def test_invalid_invite_code(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.post("/api/auth/register-with-invite", json={
            "username": "user2",
            "password": "password456",
            "display_name": "User Two",
            "invite_code": "INVALID1"
        })
        assert response.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "token" in response.json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        assert response.status_code == 401


# ============ Message Tests ============

class TestMessages:
    def setup_two_users(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        client.post("/api/auth/register-with-invite", json={
            "username": "user2",
            "password": "password456",
            "display_name": "User Two",
            "invite_code": reg.json()["invite_code"]
        })

    def test_send_message(self, client):
        self.setup_two_users(client)
        # Login
        login = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        # Send message
        response = client.post("/api/messages", json={
            "text": "Hello!"
        })
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_messages(self, client):
        self.setup_two_users(client)
        # Login
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        # Send a message
        client.post("/api/messages", json={"text": "Test"})
        # Get messages
        response = client.get("/api/messages")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        assert messages[-1]["text"] == "Test"

    def test_edit_message(self, client):
        self.setup_two_users(client)
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        # Send
        msg = client.post("/api/messages", json={"text": "Original"}).json()
        # Edit
        response = client.put(f"/api/messages/{msg['id']}", json={
            "text": "Edited"
        })
        assert response.status_code == 200
        # Verify
        messages = client.get("/api/messages").json()
        edited = [m for m in messages if m["id"] == msg["id"]][0]
        assert edited["text"] == "Edited"
        assert edited["edited"] == True

    def test_delete_message(self, client):
        self.setup_two_users(client)
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        msg = client.post("/api/messages", json={"text": "Delete me"}).json()
        response = client.delete(f"/api/messages/{msg['id']}?for_all=true")
        assert response.status_code == 200

    def test_cannot_edit_others_message(self, client):
        self.setup_two_users(client)
        # User1 sends
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        msg = client.post("/api/messages", json={"text": "Mine"}).json()
        # User2 tries to edit
        client.post("/api/auth/login", json={
            "username": "user2",
            "password": "password456"
        })
        response = client.put(f"/api/messages/{msg['id']}", json={
            "text": "Hacked!"
        })
        assert response.status_code == 403

    def test_reaction(self, client):
        self.setup_two_users(client)
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        msg = client.post("/api/messages", json={"text": "React to me"}).json()
        response = client.post(f"/api/messages/{msg['id']}/reactions", 
            data={"emoji": "❤️"})
        assert response.status_code == 200
        assert "❤️" in response.json()["reactions"]

    def test_reply(self, client):
        self.setup_two_users(client)
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        original = client.post("/api/messages", json={"text": "Original"}).json()
        reply = client.post("/api/messages", json={
            "text": "Reply",
            "reply_to": original["id"]
        })
        assert reply.status_code == 200

    def test_message_pagination(self, client):
        self.setup_two_users(client)
        client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        # Send 10 messages
        for i in range(10):
            client.post("/api/messages", json={"text": f"Message {i}"})
        # Get with limit
        response = client.get("/api/messages?limit=5")
        messages = response.json()
        assert len(messages) == 5


# ============ User Tests ============

class TestUsers:
    def test_get_me(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.get("/api/users/me")
        assert response.status_code == 200
        assert response.json()["username"] == "user1"

    def test_update_profile(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.put("/api/users/me", json={
            "display_name": "New Name",
            "bio": "Hello world"
        })
        assert response.status_code == 200

    def test_change_password(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        response = client.post("/api/auth/change-password", json={
            "old_password": "password123",
            "new_password": "newpassword456"
        })
        assert response.status_code == 200
        # Login with new password
        login = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "newpassword456"
        })
        assert login.status_code == 200


# ============ Search Tests ============

class TestSearch:
    def test_search_messages(self, client):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        client.post("/api/messages", json={"text": "Hello world"})
        client.post("/api/messages", json={"text": "Goodbye world"})
        
        response = client.get("/api/search?q=Hello")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1


# ============ Health Check ============

class TestHealth:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
