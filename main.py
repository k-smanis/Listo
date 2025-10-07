from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .database import Base, engine
from .routers import auth, tasks, admin, users, pages


# Initialize App
app = FastAPI()

# Initialize Dependencies
Base.metadata.create_all(bind=engine)


# Route to Sub-Apps
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(users.router)


# Redirect to Login Page
@app.get("/", include_in_schema=False)
async def redirect_to_login():
    return RedirectResponse(url="/ui/login/")
