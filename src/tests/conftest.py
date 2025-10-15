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
