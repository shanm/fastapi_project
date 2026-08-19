import pytest

from uuid import uuid4

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_access_token_cannot_be_used_as_refresh_token():
    user_id = uuid4()

    token = create_access_token(user_id)

    with pytest.raises(ValueError):
        decode_token(
            token,
            expected_type="refresh",
        )


def test_access_token_cannot_refresh(
    client,
    authenticated_user,
):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": authenticated_user["access_token"],
        },
    )

    assert response.status_code == 401


def test_refresh_token_cannot_access_protected_endpoint(
    client,
    authenticated_user,
):
    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": (f"Bearer {authenticated_user['refresh_token']}"),
        },
    )

    assert response.status_code == 401


def test_password_hashing():
    password = "MySecurePassword123"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_access_token():
    user_id = uuid4()

    token = create_access_token(user_id)

    decoded_user_id = decode_token(
        token,
        expected_type="access",
    )

    assert decoded_user_id == user_id


def test_refresh_token():
    user_id = uuid4()

    token = create_refresh_token(user_id)

    decoded_user_id = decode_token(
        token,
        expected_type="refresh",
    )

    assert decoded_user_id == user_id
