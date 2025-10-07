import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from starlette import status

from ..database import get_db
from ..models import Tasks
from ..utils.auth import JwtUser, get_current_user
from .conftest import TestingSessionLocal, engine


# Dependency Overrides
def override_get_db_dummy_tasks():
    """Creates a database session to your local db."""
    db_test_session = TestingSessionLocal()
    try:
        yield db_test_session
    finally:
        db_test_session.close()


def override_get_current_user_dummy_tasks():
    return JwtUser(user_id=1, username="test_user", role="user")


# Pytest Fixtures
@pytest.fixture
def client():
    # YOU HAVE TO WRITE THE client() FIXTURE LIKE THIS. HERE'S WHY:
    #     Since app.dependency_overrides is global to the FastAPI app, any override you set stays active until you remove it.
    #     By scoping overrides inside the client fixture, each test file (or test) gets its own clean set of overrides,
    #     and they’re cleared after the fixture ends so tests don’t leak into each other.
    #     This means that you save yourself from overriding `get_current_user` with `override_get_current_user_test_admin`,
    #     when you meant to override it with `override_get_current_user_test_user`
    from ..main import app

    app.dependency_overrides[get_db] = override_get_db_dummy_tasks
    app.dependency_overrides[get_current_user] = override_get_current_user_dummy_tasks
    with TestClient(app) as c:
        yield c


@pytest.fixture
def dummy_tasks():
    # create tasks
    dummy_tasks = [
        Tasks(title="task_1_title", details="task_1_details", priority=1, owner_id=1),
        Tasks(title="task_2_title", details="task_2_details", priority=2, owner_id=1),
        Tasks(title="task_3_title", details="task_3_details", priority=3, owner_id=1),
        Tasks(title="task_4_title", details="task_4_details", priority=4, owner_id=1),
    ]

    # store tasks
    db = TestingSessionLocal()
    for dummy_task in dummy_tasks:
        db.add(dummy_task)
        db.commit()

    # yield fixture
    yield dummy_tasks


@pytest.fixture
def clean_db_tasks():
    """Cleanup database after fixture-using tests"""
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tasks;"))


# Tests
def test_tasks_get_all_tasks_sc_200(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    response = client.get("/api/tasks")
    response_tasks = response.json()
    response_status_code = response.status_code

    # assert status code
    assert response_status_code == status.HTTP_200_OK

    # assert contents
    for i, dummy_task in enumerate(dummy_tasks):
        stored_task = {
            "title": dummy_task.title,
            "details": dummy_task.details,
            "priority": dummy_task.priority,
            "is_complete": dummy_task.is_complete,
            "id": dummy_task.id,
            "owner_id": dummy_task.owner_id,
        }
        assert stored_task == response_tasks[i]


def test_tasks_get_all_tasks_sc_401(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    from ..main import app

    def override_get_current_user_dummy_tasks():
        return None

    app.dependency_overrides[get_current_user] = override_get_current_user_dummy_tasks

    response = client.get("/api/tasks")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tasks_get_task_by_id_sc_200(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    for dummy_task in dummy_tasks:
        response = client.get(f"/api/tasks/{dummy_task.id}")
        response_task = response.json()
        response_status_code = response.status_code
        assert response_status_code == status.HTTP_200_OK
        assert response_task["id"] == dummy_task.id
        assert response_task["title"] == dummy_task.title
        assert response_task["details"] == dummy_task.details
        assert response_task["priority"] == dummy_task.priority
        assert response_task["owner_id"] == dummy_task.owner_id
        assert response_task["is_complete"] == dummy_task.is_complete


def test_tasks_get_task_by_id_sc_401(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    from ..main import app

    def override_get_current_user_dummy_tasks():
        return None

    app.dependency_overrides[get_current_user] = override_get_current_user_dummy_tasks

    response = client.get(f"/api/tasks/{dummy_tasks[0].id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tasks_get_task_by_id_sc_404(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    response = client.get("/api/tasks/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_tasks_post_task_sc_200(client: TestClient, clean_db_tasks):
    request_data = {
        "title": "new_task_title",
        "details": "new_task_details",
        "priority": 1,
    }
    response = client.post("/api/tasks", json=request_data)
    response_task = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert request_data["title"] == response_task["title"]
    assert request_data["details"] == response_task["details"]
    assert request_data["priority"] == response_task["priority"]


def test_tasks_post_task_sc_401(client: TestClient, clean_db_tasks):
    from ..main import app

    def override_get_current_user_dummy_tasks():
        yield None

    app.dependency_overrides[get_current_user] = override_get_current_user_dummy_tasks

    request_data = {
        "title": "new_task_title",
        "details": "new_task_details",
        "priority": 1,
    }
    response = client.post("/api/tasks", json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tasks_update_task_sc_200(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    request_data_list = [
        {
            "title": "task_1_title_updated",
            "details": "task_1_details_updated",
            "priority": 1,
            "is_complete": True,
        },
        {
            "title": "task_2_title_updated",
            "details": "task_2_details_updated",
            "priority": 2,
            "is_complete": True,
        },
        {
            "title": "task_3_title_updated",
            "details": "task_3_details_updated",
            "priority": 3,
            "is_complete": True,
        },
        {
            "title": "task_4_title_updated",
            "details": "task_4_details_updated",
            "priority": 4,
            "is_complete": True,
        },
    ]
    for i, dummy_task in enumerate(dummy_tasks):
        response = client.put(f"/api/tasks/{dummy_task.id}", json=request_data_list[i])
        response_status_code = response.status_code
        response_data = response.json()

        assert response_status_code == status.HTTP_200_OK
        assert response_data["title"] == request_data_list[i]["title"]
        assert response_data["details"] == request_data_list[i]["details"]
        assert response_data["priority"] == request_data_list[i]["priority"]
        assert response_data["is_complete"] == request_data_list[i]["is_complete"]


def test_tasks_update_task_sc_401(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    from ..main import app

    def override_get_current_user_dummy_tasks():
        yield None

    app.dependency_overrides[get_current_user] = override_get_current_user_dummy_tasks

    request_data = {
        "title": "task_1_title_updated",
        "details": "task_1_details_updated",
        "priority": 1,
        "is_complete": True,
    }
    response = client.put(f"/api/tasks/{dummy_tasks[0].id}", json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tasks_update_task_sc_404(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    request_data = {
        "title": "task_1_title_updated",
        "details": "task_1_details_updated",
        "priority": 1,
        "is_complete": True,
    }
    response = client.put("/api/tasks/999", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_tasks_delete_task_sc_200(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    for dummy_task in dummy_tasks:
        response = client.delete(f"api/tasks/{dummy_task.id}")
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.json().get("message")
            == f"Task #{dummy_task.id} was successfully deleted."
        )


def test_tasks_delete_task_sc_401(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    from ..main import app

    def override_get_current_user_dummy_tasks():
        yield None

    app.dependency_overrides[get_current_user] = override_get_current_user_dummy_tasks

    response = client.delete(f"/api/tasks/{dummy_tasks[0].id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tasks_delete_task_sc_404(
    client: TestClient, dummy_tasks: list[Tasks], clean_db_tasks
):
    response = client.delete("/api/tasks/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
