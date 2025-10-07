from fastapi import FastAPI
from .database import Base, engine
from .routers import auth, tasks, admin, users


# Initialize App
app = FastAPI()

# Initialize Dependencies
Base.metadata.create_all(bind=engine)


# Route to Sub-Apps
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(users.router)
