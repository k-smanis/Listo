from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLITE_DB_URL = "sqlite:///./listo.db"

engine = create_engine(SQLITE_DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Creates a local 'tasks.db' database session"""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
