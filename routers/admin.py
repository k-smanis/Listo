from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy import select
from routers.auth import AuthUtils
from typing import List

import models
from database import get_db
from request_response_schemas import TaskResponse
from routers.auth import JwtUser

# Initialize Router
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/tasks", response_model=List[TaskResponse], status_code=status.HTTP_200_OK)
async def get_all_tasks(
    user: JwtUser = Depends(AuthUtils.get_current_user),
    db_session: Session = Depends(get_db),
):
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    tasks = db_session.execute(select(models.Tasks)).scalars().all()
    return tasks
