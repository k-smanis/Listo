from fastapi import Depends, HTTPException, Request
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status
from dotenv import load_dotenv
from pathlib import Path
import os
from ..database import get_db
from ..utils.security import verify_password
from ..models import Users

# Initialize Auth Configuration
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv("SECRET_KEY")
assert SECRET_KEY is not None, "SECRET_KEY must be set in .env"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
ALGORITHM = os.getenv("ALGORITHM", "HS256")


class JwtUser(BaseModel):
    username: str
    user_id: int
    role: str


def get_current_user(request: Request, db_session=Depends(get_db)) -> JwtUser:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing token.",
        )

    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )

        # Optional: check user still exists
        user = db_session.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
            )

        return JwtUser(username=str(username), user_id=int(user_id), role=str(role))

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )


def authenticate_user(
    username: str, password: str, db_session: Session
) -> None | Users:
    user = db_session.execute(
        select(Users).where(Users.username == username)
    ).scalar_one_or_none()

    if not user:
        return None

    if not verify_password(
        submitted_password=password, password_hash=str(user.hashed_password)
    ):
        return None

    return user


def create_access_token(username: str, user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,  # subject claim
        "id": user_id,  # user id claim
        "role": role,
        "iat": int(now.timestamp()),  # issued at claim
        "exp": exp,  # expiration time claim
    }
    return jwt.encode(claims=payload, key=SECRET_KEY, algorithm=ALGORITHM)  # type: ignore


def create_refresh_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "username": username,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
