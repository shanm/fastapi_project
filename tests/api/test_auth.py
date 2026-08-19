def test_register_success(client, user_role):

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "john"
    assert data["email"] == "john@example.com"

    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email(client, user_role):
    payload = {
        "username": "john",
        "email": "john@example.com",
        "password": "Password123!",
    }

    first = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john2",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    assert second.status_code == 409


def test_register_duplicate_username(client, user_role):
    first = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "another@example.com",
            "password": "Password123!",
        },
    )

    assert second.status_code == 409


def test_register_invalid_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_register_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "not-an-email",
            "password": "Password123!",
        },
    )

    assert response.status_code == 422


def test_login_success(client, user_role):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "WrongPassword!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "doesnotexist@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 401


def test_get_current_user(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"


def test_get_current_user_without_token(client):
    response = client.get(
        "/api/v1/users/me",
    )

    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_refresh_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_rotation(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    old_refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert first_refresh.status_code == 200

    new_refresh_token = first_refresh.json()["refresh_token"]

    assert new_refresh_token != old_refresh_token

    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert second_refresh.status_code == 401


def test_logout(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code == 200

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 401


def test_change_password_success(
    client,
    authenticated_user,
):
    response = client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": (f"Bearer {authenticated_user['access_token']}"),
        },
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 200


def test_change_password_wrong_current_password(
    client,
    authenticated_user,
):
    response = client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": (f"Bearer {authenticated_user['access_token']}"),
        },
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 401


def test_old_password_cannot_login(
    client,
    authenticated_user,
):
    client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": (f"Bearer {authenticated_user['access_token']}"),
        },
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 401


def test_new_password_can_login(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    client.post(
        "/api/v1/auth/change-password",
        headers={
            "Authorization": (f"Bearer {login_response.json()['access_token']}"),
        },
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "NewPassword123!",
        },
    )

    assert response.status_code == 200
