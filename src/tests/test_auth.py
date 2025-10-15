import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from fastapi import Response
from starlette import status
from datetime import timedelta

from ..database import get_db
from ..models import Users
from ..utils.security import hash_password
from ..utils.auth import create_refresh_token
from .conftest import TestingSessionLocal, engine


# Dummy Data
test_user_passwords = [
    "test_user_1_password",
    "test_user_2_password",
    "test_user_3_password",
]

test_user_phone_numbers = [
    "4153928472",
    "6285301946",
    "2138745093",
]


# Dependency Overrides
def override_get_db_test_auth():
    """Creates a database session to your local db."""
    db_test_session = TestingSessionLocal()
    try:
        yield db_test_session
    finally:
        db_test_session.close()


# Fixtures
@pytest.fixture
def client():
    from ..main import app

    app.dependency_overrides[get_db] = override_get_db_test_auth
    with TestClient(app) as c:
        yield c


@pytest.fixture
def clean_db_auth():
    """Cleanup database after fixture-using tests"""
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users;"))


@pytest.fixture
def dummy_users():
    # create dummy users
    dummy_users = [
        Users(
            role="user",
            username="test_user_1",
            first_name="test_user_1_FIRST_NAME",
            last_name="test_user_1_LAST_NAME",
            hashed_password=hash_password(test_user_passwords[0]),
            email="tu1@mail.com",
            phone_number=test_user_phone_numbers[0],
        ),
        Users(
            role="user",
            username="test_user_2",
            first_name="test_user_2_FIRST_NAME",
            last_name="test_user_2_LAST_NAME",
            hashed_password=hash_password(test_user_passwords[1]),
            email="tu2@mail.com",
            phone_number=test_user_phone_numbers[1],
        ),
        Users(
            role="admin",
            username="test_user_3",
            first_name="test_user_3_FIRST_NAME",
            last_name="test_user_3_LAST_NAME",
            hashed_password=hash_password(test_user_passwords[2]),
            email="tu3@mail.com",
            phone_number=test_user_phone_numbers[1],
        ),
    ]

    # store dummy users
    db_session = TestingSessionLocal()
    for dummy_user in dummy_users:
        db_session.add(dummy_user)
        db_session.commit()

    # yield fixture
    yield dummy_users


# Tests
@pytest.mark.parametrize("user_id", [1, 2, 3])
def test_auth_login_for_access_token_sc_200(
    client: TestClient, user_id: int, dummy_users: list[Users], clean_db_auth
):
    user_idx = user_id - 1
    auth_data = {
        "username": dummy_users[user_idx].username,
        "password": test_user_passwords[user_idx],
    }

    response = client.post("/api/token", data=auth_data)
    body = response.json()
    cookies = response.cookies

    # --- assertions ---
    assert response.status_code == status.HTTP_200_OK
    assert "message" in body
    assert body["message"].lower().startswith("login successful")
    assert "access_token" in cookies
    assert len(cookies.get("access_token")) > 20  # type: ignore # looks like a JWT


def test_auth_login_for_access_token_sc_401(
    client: TestClient, dummy_users: list[Users], clean_db_auth
):
    auth_data = {
        "username": dummy_users[1].username,
        "password": "dummy_wrong_password",
    }

    response = client.post("/api/token", data=auth_data)

    # --- assertions ---
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_get_refresh_token_sc_200(
    client: TestClient, dummy_users: list[Users], clean_db_auth
):
    user = dummy_users[0]

    # Create a valid refresh token
    refresh_token = create_refresh_token(
        username=user.username,  # type: ignore
        user_id=user.id,  # type: ignore
        role=user.role,  # type: ignore
        expires_delta=timedelta(days=1),
    )

    # Attach token as cookie
    response = client.post("/api/refresh", cookies={"refresh_token": refresh_token})
    body = response.json()

    # --- assertions ---
    assert response.status_code == status.HTTP_200_OK
    assert "message" in body
    assert body["message"].lower().startswith("access token refreshed")
    assert "access_token" in response.cookies
    assert len(response.cookies.get("access_token")) > 20  # type: ignore


def test_auth_get_refresh_token_sc_401_missing_refresh_token(client: TestClient):
    response = client.post("/api/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_get_refresh_token_sc_401_expired_refresh_token(
    client: TestClient, dummy_users: list[Users], clean_db_auth
):
    user = dummy_users[0]

    # Create an expired refresh token
    expired_token = create_refresh_token(
        username=user.username,  # type: ignore
        user_id=user.id,  # type: ignore
        role=user.role,  # type: ignore
        expires_delta=timedelta(seconds=-10),  # expired already
    )

    response = client.post("/api/refresh", cookies={"refresh_token": expired_token})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
