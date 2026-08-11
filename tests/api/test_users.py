from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/api/v1/users/", json={"email": "test@example.com", "password": "123456"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"