from fastapi import APIRouter, HTTPException, Depends, Path, Body, Response
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
from routers.auth import AuthUtils
from typing import List

import models
from database import get_db
from request_response_schemas import TaskCreate, TaskUpdate, TaskResponse
from routers.auth import JwtUser

# Initialize Router
router = APIRouter(prefix="/api", tags=["Tasks"])


@router.get("/tasks", response_model=List[TaskResponse], status_code=status.HTTP_200_OK)
async def get_all_tasks(
    user: JwtUser = Depends(AuthUtils.get_current_user),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    tasks = (
        db_session.execute(
            select(models.Tasks).where(models.Tasks.owner_id == user.user_id)
        )
        .scalars()
        .all()
    )
    return tasks


@router.get(
    "/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK
)
async def get_task_by_id(
    user: JwtUser = Depends(AuthUtils.get_current_user),
    task_id: int = Path(gt=0),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    target_task = db_session.execute(
        select(models.Tasks).where(
            models.Tasks.id == task_id, models.Tasks.owner_id == user.user_id
        )
    ).scalar_one_or_none()

    if target_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task (#{task_id}) not found. It likely doesn't exist.",
        )

    return target_task


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def post_task(
    response: Response,
    user: JwtUser = Depends(AuthUtils.get_current_user),
    request_body: TaskCreate = Body(...),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    new_task = models.Tasks(**request_body.model_dump())
    new_task.owner_id = user.user_id  # type: ignore

    try:
        db_session.add(new_task)
        db_session.commit()
        db_session.refresh(new_task)

    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Constraint violation."
        )

    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error."
        )

    response.headers["Location"] = f"/tasks/{new_task.id}"  # Created Resource URL
    return new_task


@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    user: JwtUser = Depends(AuthUtils.get_current_user),
    task_id: int = Path(gt=0),
    updated_task: TaskUpdate = Body(...),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    db_task = db_session.get(models.Tasks, task_id)

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task (#{task_id}) not found.",
        )
    else:
        for field, value in updated_task.model_dump(exclude_unset=True).items():
            setattr(db_task, field, value)

    try:
        db_session.add(db_task)
        db_session.commit()
        db_session.refresh(db_task)

    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Constraint violation."
        )

    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error."
        )

    return db_task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
    user: JwtUser = Depends(AuthUtils.get_current_user),
    task_id: int = Path(gt=0),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    db_task = db_session.get(models.Tasks, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task (#{task_id}) not found.",
        )

    try:
        db_session.delete(db_task)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Constraint violation."
        )

    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
        )

    return {"message": f"Task #{task_id} was successfully deleted."}
