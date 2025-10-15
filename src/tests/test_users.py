import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from starlette import status

from ..database import get_db
from ..models import Users
from ..utils.auth import JwtUser, get_current_user
from ..utils.security import hash_password, verify_password
from .conftest import TestingSessionLocal, engine

# Dummy Data
test_user_passwords = [
    "test_user_1_password",
    "test_user_2_password",
    "test_user_3_password",
]

test_user_passwords_changed = [
    "test_user_1_password_changed",
    "test_user_2_password_changed",
    "test_user_3_password_changed",
]

test_user_phone_numbers = [
    "(415) 392-8472",
    "(628) 530-1946",
    "(213) 874-5093",
]

test_user_phone_numbers_changed = [
    "(415) 392-8473",
    "(628) 530-1947",
    "(213) 874-5094",
]


# Dependency Overrides
def override_get_db_test_users():
    """Creates a database session to your local db."""
    db_test_session = TestingSessionLocal()
    try:
        yield db_test_session
    finally:
        db_test_session.close()


def override_get_current_user_test_users():
    yield JwtUser(user_id=1, username="test_user_1", role="user")


# Pytest Fixtures
@pytest.fixture
def client():
    from ..main import app

    app.dependency_overrides[get_db] = override_get_db_test_users
    app.dependency_overrides[get_current_user] = override_get_current_user_test_users
    with TestClient(app) as c:
        yield c


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


@pytest.fixture
def clean_db_users():
    """Cleanup database after fixture-using tests"""
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users;"))


# Tests
def test_users_create_user_sc_201(client: TestClient, clean_db_users):
    dummy_users = [
        {
            "role": "user",
            "username": "test_user_1",
            "first_name": "test_user_1_FIRST_NAME",
            "last_name": "test_user_1_LAST_NAME",
            "password": test_user_passwords[0],
            "email": "tu1@mail.com",
            "phone_number": test_user_phone_numbers[0],
        },
        {
            "role": "user",
            "username": "test_user_2",
            "first_name": "test_user_2_FIRST_NAME",
            "last_name": "test_user_2_LAST_NAME",
            "password": test_user_passwords[1],
            "email": "tu2@mail.com",
            "phone_number": test_user_phone_numbers[1],
        },
        {
            "role": "admin",
            "username": "test_user_3",
            "first_name": "test_user_3_FIRST_NAME",
            "last_name": "test_user_3_LAST_NAME",
            "password": test_user_passwords[2],
            "email": "tu3@mail.com",
            "phone_number": test_user_phone_numbers[2],
        },
    ]
    for dummy_user in dummy_users:
        response = client.post("/api/users", json=dummy_user)
        response_data = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert dummy_user["username"] == response_data["username"]
        assert dummy_user["email"] == response_data["email"]
        assert dummy_user["first_name"].capitalize() == response_data["first_name"]
        assert dummy_user["last_name"].capitalize() == response_data["last_name"]
        assert verify_password(
            submitted_password=dummy_user["password"],
            password_hash=response_data["hashed_password"],
        )
        assert dummy_user["role"] == response_data["role"]
        assert dummy_user["phone_number"] == response_data["phone_number"]


def test_users_create_user_sc_409(client: TestClient, clean_db_users):
    dummy_user = [
        {
            "role": "user",
            "username": "test_user_1",
            "first_name": "test_user_1_FIRST_NAME",
            "last_name": "test_user_1_LAST_NAME",
            "password": test_user_passwords[0],
            "email": "tu1@mail.com",
            "phone_number": test_user_phone_numbers[0],
        },
        {
            "role": "user",
            "username": "test_user_1",
            "first_name": "test_user_1_FIRST_NAME",
            "last_name": "test_user_1_LAST_NAME",
            "password": test_user_passwords[0],
            "email": "tu1@mail.com",
            "phone_number": test_user_phone_numbers[0],
        },
    ]

    response_1 = client.post("/api/users", json=dummy_user[0])
    assert response_1.status_code == status.HTTP_201_CREATED

    response_2 = client.post("/api/users", json=dummy_user[1])
    assert response_2.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize("user_id", [1, 2, 3])
def test_users_get_user_sc_200(
    client: TestClient, user_id: int, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield JwtUser(user_id=user_id, username=f"test_user_{user_id}", role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/api/users")
    response_data = response.json()
    dummy_idx = user_id - 1

    assert response.status_code == status.HTTP_200_OK
    assert response_data["email"] == dummy_users[dummy_idx].email
    assert response_data["first_name"] == dummy_users[dummy_idx].first_name
    assert response_data["last_name"] == dummy_users[dummy_idx].last_name
    assert response_data["hashed_password"] == dummy_users[dummy_idx].hashed_password
    assert response_data["role"] == dummy_users[dummy_idx].role
    assert response_data["phone_number"] == dummy_users[dummy_idx].phone_number


def test_users_get_user_sc_401(
    client: TestClient, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield None

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/api/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_users_get_user_sc_409(
    client: TestClient, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield JwtUser(username="non-existent-user", user_id=999, role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/api/users")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("user_id", [1, 2, 3])
def test_users_change_password_sc_200(
    client: TestClient, user_id: int, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user_test_users():
        yield JwtUser(user_id=user_id, username=f"test_user_{user_id}", role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user_test_users

    pwd_idx = user_id - 1
    user_verification = {
        "password": test_user_passwords[pwd_idx],
        "new_password": test_user_passwords_changed[pwd_idx],
    }
    response = client.put("/api/password", json=user_verification)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_users_change_password_sc_401_no_auth(
    client: TestClient, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield None

    app.dependency_overrides[get_current_user] = override_get_current_user

    user_verification = {
        "password": test_user_passwords[0],
        "new_password": test_user_passwords_changed[0],
    }
    response = client.put("/api/password", json=user_verification)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_users_change_password_sc_401_wrong_password(
    client: TestClient, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield JwtUser(
            username=dummy_users[0].username,  # type: ignore
            user_id=dummy_users[0].id,  # type: ignore
            role=dummy_users[0].role,  # type: ignore
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    user_verification = {
        "password": "wreng pasword",
        "new_password": test_user_passwords_changed[0],
    }
    response = client.put("/api/password", json=user_verification)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("user_id", [1, 2, 3])
def test_users_change_phone_number(
    client: TestClient, user_id: int, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user_test_users():
        yield JwtUser(user_id=user_id, username=f"test_user_{user_id}", role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user_test_users

    pwd_idx = user_id - 1
    phone_change = {
        "password": test_user_passwords[pwd_idx],
        "new_phone_number": test_user_phone_numbers_changed[pwd_idx],
    }
    response = client.put("/api/phone-number", json=phone_change)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_users_change_phone_number_sc_401_no_auth(
    client: TestClient, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield None

    app.dependency_overrides[get_current_user] = override_get_current_user

    user_verification = {
        "password": test_user_passwords[0],
        "new_phone_number": test_user_phone_numbers_changed[0],
    }
    response = client.put("/api/phone-number", json=user_verification)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_users_change_phone_number_sc_401_wrong_password(
    client: TestClient, dummy_users: list[Users], clean_db_users
):
    from ..main import app

    def override_get_current_user():
        yield JwtUser(
            username=dummy_users[0].username,  # type: ignore
            user_id=dummy_users[0].id,  # type: ignore
            role=dummy_users[0].role,  # type: ignore
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    user_verification = {
        "password": "wreng pasword",
        "new_phone_number": test_user_phone_numbers_changed[0],
    }
    response = client.put("/api/phone-number", json=user_verification)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
