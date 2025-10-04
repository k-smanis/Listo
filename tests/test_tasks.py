import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from starlette import status

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
def override_get_db_test_tasks():
    """Creates a database session to your local db."""
    db_test_session = TestingSessionLocal()
    try:
        yield db_test_session
    finally:
        db_test_session.close()


def override_get_current_user_test_tasks():
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

    app.dependency_overrides[get_db] = override_get_db_test_tasks
    app.dependency_overrides[get_current_user] = override_get_current_user_test_tasks
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_task():
    # create & store task
    task = Tasks(title="task_1_title", details="task_1_details", priority=1, owner_id=1)
    db = TestingSessionLocal()
    db.add(task)
    db.commit()

    # return task
    yield task

    # cleanup database after fixture-using tests
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM tasks;"))
        connection.commit()


# Tests
def test_tasks_get_all_tasks(
    client,
):
    pass


def test_tasks_get_task_by_id(
    client,
):
    pass


def test_tasks_post_task(
    client,
):
    pass


def test_tasks_update_task(
    client,
):
    pass


def test_tasks_delete_task(
    client,
):
    pass
