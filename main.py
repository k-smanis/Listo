from fastapi import FastAPI
from routers import auth, tasks, admin, users

import database


# Initialize App
app = FastAPI()

# Initialize Dependencies
database.Base.metadata.create_all(bind=database.engine)

# Route to Sub-Apps
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(users.router)
