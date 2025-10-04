from fastapi import FastAPI
from .database import Base, engine
from starlette import status
from .routers import auth, tasks, admin, users


# Initialize App
app = FastAPI()

# Initialize Dependencies
Base.metadata.create_all(bind=engine)


# Test Endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}


# Route to Sub-Apps
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(users.router)
