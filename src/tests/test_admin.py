import pytest

from fastapi.testclient import TestClient
from starlette import status
from sqlalchemy import text

from ..database import get_db
from ..models import Tasks
from ..utils.auth import JwtUser, get_current_user
from .conftest import TestingSessionLocal, engine


# Dependency Overrides
def override_get_db_test_admin():
    """Creates a database session to your local db."""
    db_test_session = TestingSessionLocal()
    try:
        yield db_test_session
    finally:
        db_test_session.close()


def override_get_current_user_test_admin():
    return JwtUser(user_id=1, username="test_user", role="admin")


# Pytest Fixtures
@pytest.fixture
def client():
    from ..main import app

    app.dependency_overrides[get_db] = override_get_db_test_admin
    app.dependency_overrides[get_current_user] = override_get_current_user_test_admin
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_tasks():
    # create tasks
    test_tasks = [
        Tasks(title="task_1_title", details="task_1_details", priority=1, owner_id=1),
        Tasks(title="task_2_title", details="task_2_details", priority=1, owner_id=2),
        Tasks(title="task_3_title", details="task_3_details", priority=1, owner_id=3),
        Tasks(title="task_4_title", details="task_4_details", priority=1, owner_id=4),
    ]

    # store tasks
    db = TestingSessionLocal()
    for task in test_tasks:
        db.add(task)
        db.commit()

    # yield tasks
    yield test_tasks

    # cleanup database after fixture-using tests
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM tasks;"))
        connection.commit()


@pytest.fixture
def clean_db():
    """Cleanup database after fixture-using tests"""
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tasks;"))


# Tests
def test_admin_get_all_tasks_sc_200(
    client: TestClient, test_tasks: list[Tasks], clean_db
):
    response = client.get("/api/admin/tasks")
    response_tasks = response.json()
    assert response.status_code == status.HTTP_200_OK

    for i, test_task in enumerate(test_tasks):
        stored_tasks = {
            "title": test_task.title,
            "details": test_task.details,
            "priority": test_task.priority,
            "is_complete": test_task.is_complete,
            "id": test_task.id,
            "owner_id": test_task.owner_id,
        }
        assert response_tasks[i] == stored_tasks


def test_admin_get_all_tasks_sc_401(
    client: TestClient, test_tasks: list[Tasks], clean_db
):
    from ..main import app

    def override_get_current_user_test_admin():
        return JwtUser(user_id=1, username="test_user", role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user_test_admin

    response = client.get("/api/admin/tasks")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
