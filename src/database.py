from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
from pathlib import Path
import os


# Production Database Setup (POSTGRES)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDATABASE = os.getenv("PGDATABASE")

POSTGRES_DB_URL = URL.create(
    "postgresql+psycopg2",
    username=PGUSER,
    password=PGPASSWORD,
    host=PGHOST,
    port=int(PGPORT) if PGPORT else None,  # omit if missing
    database=PGDATABASE,
)

engine = create_engine(POSTGRES_DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Creates a database session to your local db."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
