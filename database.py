from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
import urllib.parse

# SQLITE Setup
# SQLITE_DB_URL = "sqlite:///./listo.db"
# engine = create_engine(SQLITE_DB_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


# POSTGRES Setup
load_dotenv()
PGUSER = os.getenv("PGUSER")
PGPASSWORD = urllib.parse.quote_plus(os.getenv("PGPASSWORD", ""))
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDATABASE = os.getenv("PGDATABASE")
POSTGRES_DB_URL = (
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
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
