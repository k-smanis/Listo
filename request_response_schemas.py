from pydantic import BaseModel, Field
from typing import Optional


# shared fields clients can set
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    details: Optional[str] = None
    priority: int = Field(1, ge=1, le=5)
    # exclude things like owner_id if you don't want clients setting them


# POST /tasks
class TaskCreate(TaskBase):
    pass


# PUT /tasks/{id}
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    details: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_complete: Optional[bool] = None


# What you return to clients
class TaskResponse(TaskBase):
    is_complete: bool
    id: int
