import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from starlette import status

from ..database import get_db
from ..models import Users
from ..utils.security import hash_password
from .conftest import TestingSessionLocal, engine


# Dummy Data
test_user_passwords = [
    "test_user_1_password",
    "test_user_2_password",
    "test_user_3_password",
]

test_user_phone_numbers = [
    "(415) 392-8472",
    "(628) 530-1946",
    "(213) 874-5093",
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
    # YOU HAVE TO WRITE THE client() FIXTURE LIKE THIS. HERE'S WHY:
    #     Since app.dependency_overrides is global to the FastAPI app, any override you set stays active until you remove it.
    #     By scoping overrides inside the client fixture, each test file (or test) gets its own clean set of overrides,
    #     and they’re cleared after the fixture ends so tests don’t leak into each other.
    #     This means that you save yourself from overriding `get_current_user` with `override_get_current_user_test_admin`,
    #     when you meant to override it with `override_get_current_user_test_user`
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

    # The endpoint parses the request's sign-in data using OAuth2PasswordRequestForm
    # which itself parses application/x-www-form-urlencoded and not JSON.
    # So we have to pass the mock sign-in data using the `data=...` parameter instead
    # of the `json=...` parameter.
    response = client.post("/api/token", data=auth_data)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["token_type"] == "bearer"


def test_auth_login_for_access_token_sc_401(
    client: TestClient, dummy_users: list[Users], clean_db_auth
):
    auth_data = {
        "username": dummy_users[1].username,
        "password": "dummy_wrong_passwerd",
    }

    # The endpoint parses the request's sign-in data using OAuth2PasswordRequestForm
    # which itself parses application/x-www-form-urlencoded and not JSON.
    # So we have to pass the mock sign-in data using the `data=...` parameter instead
    # of the `json=...` parameter.
    response = client.post("/api/token", data=auth_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
