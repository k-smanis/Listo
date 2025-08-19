from fastapi import FastAPI, HTTPException, Depends, Path, Body, Response
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select

from typing import List

import database
import models
from request_response_schemas import TaskCreate, TaskUpdate, TaskResponse

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


@app.get("/tasks", response_model=List[TaskResponse])
async def get_all_tasks(
    db_session: Session = Depends(get_db),
):
    tasks = db_session.execute(select(models.Tasks)).scalars().all()
    return tasks


@app.get(
    "/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK
)
async def get_task_by_id(
    task_id: int = Path(gt=0), db_session: Session = Depends(get_db)
):
    target_task = db_session.execute(
        select(models.Tasks).where(models.Tasks.id == task_id)
    ).scalar_one_or_none()

    if target_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task (#{task_id}) not found. It likely doesn't exist.",
        )

    return target_task


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def post_task(
    response: Response,
    request_body: TaskCreate = Body(...),
    db_session: Session = Depends(get_db),
):
    new_task = models.Tasks(**request_body.model_dump())
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


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    task_id: int = Path(gt=0),
    updated_task: TaskUpdate = Body(...),
    db_session: Session = Depends(get_db),
):
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


@app.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(task_id: int = Path(gt=0), db_session: Session = Depends(get_db)):
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
