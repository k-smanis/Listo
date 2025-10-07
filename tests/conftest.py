import pytest
from sqlalchemy import create_engine
from ..database import Base
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Test Database Setup (SQLITE)
SQLITE_DB_URL = "sqlite:///./test_listo.db"
engine = create_engine(
    SQLITE_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)  # optional


# TODO: Notes
# A conftest.py file is a special pytest hook file that pytest automatically discovers and loads. It’s typically used to define shared fixtures that can be reused across multiple test files without needing to import them manually.
# In this example, the setup_db fixture is declared with scope="session" and autouse=True.
# scope="session" means the fixture runs only once for the entire test session (before the first test and after the last test).
# autouse=True makes pytest apply the fixture automatically, without explicitly listing it in test functions.
# Mechanically, this fixture ensures the database schema is created at the start of the test session (Base.metadata.create_all), and then cleaned up when the session finishes (Base.metadata.drop_all). This way, all tests can rely on the database schema being ready, while keeping setup logic centralized and DRY.
