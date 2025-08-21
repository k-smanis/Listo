from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from pydantic import BaseModel

from request_response_schemas import CreateUser, Token
from database import get_db
import models
from security import hash_password, verify_password

# Intialize Router
router = APIRouter(prefix="/api", tags=["Auth"])

# Initialize Auth Configuration
load_dotenv()
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


class AuthUtils:
    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme)) -> JwtUser:
        try:
            payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
            username = payload.get("sub")  # type: ignore
            user_id = payload.get("id")  # type: ignore
            role = payload.get("role")  # type: ignore
            if username is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            else:
                return JwtUser(
                    username=str(username), user_id=int(user_id), role=str(role)
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

    @staticmethod
    def authenticate_user(
        username: str, password: str, db_session: Session
    ) -> None | models.Users:
        user = db_session.execute(
            select(models.Users).where(models.Users.username == username)
        ).scalar_one_or_none()

        if not user:
            return None

        if not verify_password(
            submitted_password=password, password_hash=str(user.hashed_password)
        ):
            return None

        return user

    @staticmethod
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


@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(
    create_user_request: CreateUser = Body(...), db_session: Session = Depends(get_db)
):
    new_user = models.Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name.capitalize(),
        last_name=create_user_request.last_name.capitalize(),
        role=create_user_request.role,
        hashed_password=hash_password(create_user_request.password),
        is_active=True,
    )

    try:
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)

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


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: Session = Depends(get_db),
):
    user: None | models.Users = AuthUtils.authenticate_user(
        username=form_data.username, password=form_data.password, db_session=db_session
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )
    else:
        token = AuthUtils.create_access_token(
            username=form_data.username, user_id=user.id, role=user.role  # type: ignore
        )
        return {"access_token": token, "token_type": "bearer"}
