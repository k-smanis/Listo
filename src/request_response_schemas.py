from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, ClassVar
import re


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


# GET /users
class CreateUser(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=50)
    phone_number: str | None = Field(None, pattern=r"^\+?\d{7,15}$")
    role: str = Field("user")

    name_pattern: ClassVar[re.Pattern] = re.compile(r"^[A-Za-z\s]+$")

    @field_validator("first_name", "last_name")
    def validate_names(cls, v: str):
        if not cls.name_pattern.match(v):
            raise ValueError("Only Latin letters and spaces are allowed.")
        return v.strip().capitalize()

    @field_validator("role")
    def restrict_role(cls, role: str):
        if role.lower() == "admin":
            raise ValueError("You are not allowed to create an admin account.")
        return role.lower()


# What you return to clients
class UserResponse(BaseModel):
    username: str = Field()
    email: str = Field()
    first_name: str = Field()
    last_name: str = Field()
    hashed_password: str = Field()
    role: str = Field()
    phone_number: str = Field()


class TaskResponse(TaskBase):
    is_complete: bool
    id: int
    owner_id: int


class Token(BaseModel):
    access_token: str
    token_type: str


class UserVerification(BaseModel):
    password: str
    new_password: str = Field(..., min_length=8, max_length=50)


class PhoneChange(BaseModel):
    password: str
    new_phone_number: str | None = Field(None, pattern=r"^\+?\d{7,15}$")
