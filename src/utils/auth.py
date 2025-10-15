from fastapi import Depends, HTTPException
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..utils.security import verify_password
from ..models import Users
from starlette import status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from pathlib import Path
import os

# Initialize Auth Configuration
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv("SECRET_KEY")
assert SECRET_KEY is not None, "SECRET_KEY must be set in .env"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Initialize Dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class JwtUser(BaseModel):
    username: str
    user_id: int
    role: str


def get_current_user(token: str = Depends(oauth2_scheme)) -> JwtUser:
    try:
        payload = jwt.decode(
            token=token, key=SECRET_KEY, algorithms=[ALGORITHM]  # type: ignore
        )
        username = payload.get("sub")  # type: ignore
        user_id = payload.get("id")  # type: ignore
        role = payload.get("role")  # type: ignore
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        else:
            return JwtUser(username=str(username), user_id=int(user_id), role=str(role))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
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
