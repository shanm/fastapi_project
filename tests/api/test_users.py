from fastapi.testclient import TestClient

from app.main import app


def test_register_user(client) -> None:
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "testuser22223333",
            "email": "test123@example.com",
            "password": "p@ssword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser22223333"
    assert data["email"] == "test123@example.com"
