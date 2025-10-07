from typing import List

from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Tasks
from ..database import get_db
from ..request_response_schemas import TaskResponse
from ..utils.auth import JwtUser, get_current_user

# Initialize Router
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/tasks", response_model=List[TaskResponse], status_code=status.HTTP_200_OK)
async def get_all_tasks(
    user: JwtUser = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    # breakpoint()
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    tasks = db_session.execute(select(Tasks)).scalars().all()
    return tasks
