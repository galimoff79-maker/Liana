"""
Backend tests for ПриватЧат
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ============ Auth Tests ============

class TestRegistration:
    def test_register_first_user(self):
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

    def test_register_second_user_with_invite(self):
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

    def test_register_third_user_blocked(self):
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

    def test_register_duplicate_username(self):
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

    def test_register_short_password(self):
        response = client.post("/api/auth/register", json={
            "username": "user1",
            "password": "12345",
            "display_name": "User One"
        })
        assert response.status_code == 400

    def test_register_short_username(self):
        response = client.post("/api/auth/register", json={
            "username": "ab",
            "password": "password123",
            "display_name": "User One"
        })
        assert response.status_code == 400

    def test_invalid_invite_code(self):
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
    def test_login_success(self):
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

    def test_login_wrong_password(self):
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

    def test_login_nonexistent_user(self):
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        assert response.status_code == 401


# ============ Message Tests ============

class TestMessages:
    def get_auth_header(self, username="user1", password="password123"):
        login = client.post("/api/auth/login", json={
            "username": username,
            "password": password
        })
        token = login.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def setup_two_users(self):
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

    def test_send_message(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        response = client.post("/api/messages", json={
            "text": "Hello!"
        }, headers=headers)
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_messages(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        # Send a message
        client.post("/api/messages", json={"text": "Test"}, headers=headers)
        # Get messages
        response = client.get("/api/messages", headers=headers)
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        assert messages[-1]["text"] == "Test"

    def test_edit_message(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        # Send
        msg = client.post("/api/messages", json={"text": "Original"}, headers=headers).json()
        # Edit
        response = client.put(f"/api/messages/{msg['id']}", json={
            "text": "Edited"
        }, headers=headers)
        assert response.status_code == 200
        # Verify
        messages = client.get("/api/messages", headers=headers).json()
        edited = [m for m in messages if m["id"] == msg["id"]][0]
        assert edited["text"] == "Edited"
        assert edited["edited"] == True

    def test_delete_message(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        msg = client.post("/api/messages", json={"text": "Delete me"}, headers=headers).json()
        response = client.delete(f"/api/messages/{msg['id']}?for_all=true", headers=headers)
        assert response.status_code == 200

    def test_cannot_edit_others_message(self):
        self.setup_two_users()
        headers1 = self.get_auth_header("user1", "password123")
        headers2 = self.get_auth_header("user2", "password456")
        # User1 sends
        msg = client.post("/api/messages", json={"text": "Mine"}, headers=headers1).json()
        # User2 tries to edit
        response = client.put(f"/api/messages/{msg['id']}", json={
            "text": "Hacked!"
        }, headers=headers2)
        assert response.status_code == 403

    def test_reaction(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        msg = client.post("/api/messages", json={"text": "React to me"}, headers=headers).json()
        response = client.post(f"/api/messages/{msg['id']}/reactions", 
            data={"emoji": "❤️"}, headers=headers)
        assert response.status_code == 200
        assert "❤️" in response.json()["reactions"]

    def test_reply(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        original = client.post("/api/messages", json={"text": "Original"}, headers=headers).json()
        reply = client.post("/api/messages", json={
            "text": "Reply",
            "reply_to": original["id"]
        }, headers=headers)
        assert reply.status_code == 200

    def test_message_pagination(self):
        self.setup_two_users()
        headers = self.get_auth_header()
        # Send 10 messages
        for i in range(10):
            client.post("/api/messages", json={"text": f"Message {i}"}, headers=headers)
        # Get with limit
        response = client.get("/api/messages?limit=5", headers=headers)
        messages = response.json()
        assert len(messages) == 5


# ============ User Tests ============

class TestUsers:
    def get_auth_header(self):
        login = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        return {"Authorization": f"Bearer {login.json()['token']}"}

    def test_get_me(self):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        headers = self.get_auth_header()
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["username"] == "user1"

    def test_update_profile(self):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        headers = self.get_auth_header()
        response = client.put("/api/users/me", json={
            "display_name": "New Name",
            "bio": "Hello world"
        }, headers=headers)
        assert response.status_code == 200

    def test_change_password(self):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        headers = self.get_auth_header()
        response = client.post("/api/auth/change-password", json={
            "old_password": "password123",
            "new_password": "newpassword456"
        }, headers=headers)
        assert response.status_code == 200
        # Login with new password
        login = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "newpassword456"
        })
        assert login.status_code == 200


# ============ Search Tests ============

class TestSearch:
    def get_auth_header(self):
        login = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        return {"Authorization": f"Bearer {login.json()['token']}"}

    def test_search_messages(self):
        client.post("/api/auth/register", json={
            "username": "user1",
            "password": "password123",
            "display_name": "User One"
        })
        headers = self.get_auth_header()
        client.post("/api/messages", json={"text": "Hello world"}, headers=headers)
        client.post("/api/messages", json={"text": "Goodbye world"}, headers=headers)
        
        response = client.get("/api/search?q=Hello", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1


# ============ Health Check ============

class TestHealth:
    def test_health(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
