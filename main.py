from fastapi import FastAPI

import database
import models

# Initialize App
app = FastAPI()

# Initialize Database
database.Base.metadata.create_all(bind=database.engine)


def get_db():
    """Creates a local 'tasks.db' database session"""
    db_session = database.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
