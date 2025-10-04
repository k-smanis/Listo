import pytest

from fastapi.testclient import TestClient
from starlette import status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..database import Base, get_db
from ..models import Tasks
from ..utils.auth import JwtUser, get_current_user


# Test Database Setup (SQLITE)
SQLITE_DB_URL = "sqlite:///./test_listo.db"
engine = create_engine(
    SQLITE_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    # YOU HAVE TO WRITE THE client() FIXTURE LIKE THIS. HERE'S WHY:
    #     Since app.dependency_overrides is global to the FastAPI app, any override you set stays active until you remove it.
    #     By scoping overrides inside the client fixture, each test file (or test) gets its own clean set of overrides,
    #     and they’re cleared after the fixture ends so tests don’t leak into each other.
    #     This means that you save yourself from overriding `get_current_user` with `override_get_current_user_test_admin`,
    #     when you meant to override it with `override_get_current_user_test_user`
    from ..main import app

    app.dependency_overrides[get_db] = override_get_db_test_admin
    app.dependency_overrides[get_current_user] = override_get_current_user_test_admin
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_tasks():
    # create & store task
    test_tasks = [
        Tasks(title="task_1_title", details="task_1_details", priority=1, owner_id=1),
        Tasks(title="task_2_title", details="task_2_details", priority=1, owner_id=2),
        Tasks(title="task_3_title", details="task_3_details", priority=1, owner_id=3),
        Tasks(title="task_4_title", details="task_4_details", priority=1, owner_id=4),
    ]

    db = TestingSessionLocal()

    for task in test_tasks:
        db.add(task)
        db.commit()

    yield test_tasks

    # cleanup database after fixture-using tests
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM tasks;"))
        connection.commit()


# Tests
def test_admin_get_all_tasks(test_tasks: list[Tasks], client: TestClient):
    response = client.get("/api/admin/tasks")
    response_tasks = response.json()
    assert response.status_code == status.HTTP_200_OK

    for i, test_task in enumerate(test_tasks):
        stored_tasks = {
            "id": test_task.id,
            "title": test_task.title,
            "details": test_task.details,
            "priority": test_task.priority,
            "is_complete": test_task.is_complete,
            "owner_id": test_task.owner_id,
        }
        assert response_tasks[i] == stored_tasks
