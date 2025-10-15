from fastapi import APIRouter, HTTPException, Depends, Body
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select

from ..models import Users
from ..database import get_db
from ..request_response_schemas import (
    PhoneChange,
    UserVerification,
    CreateUser,
    UserResponse,
)
from ..utils.auth import JwtUser, get_current_user
from ..utils.security import hash_password, verify_password

# Initialize Router
router = APIRouter(prefix="/api", tags=["Users"])


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    create_user_request: CreateUser = Body(...),
    response_model=UserResponse,
    db_session: Session = Depends(get_db),
):
    new_user = Users(
        username=create_user_request.username.strip(),
        email=create_user_request.email.strip(),
        first_name=create_user_request.first_name.capitalize(),
        last_name=create_user_request.last_name.capitalize(),
        hashed_password=hash_password(create_user_request.password),
        phone_number=create_user_request.phone_number,
        role=create_user_request.role,
        is_active=True,
    )

    try:
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        return {
            "username": new_user.username,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "hashed_password": new_user.hashed_password,
            "role": new_user.role,
            "phone_number": new_user.phone_number,
        }

    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This account likely already exists.",
        )

    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error."
        )


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_user(
    user: JwtUser = Depends(get_current_user),
    response_model=UserResponse,
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    target_user: Users = db_session.execute(
        select(Users).where(Users.id == user.user_id)
    ).scalar_one_or_none()

    if target_user:
        return {
            "username": target_user.username,
            "email": target_user.email,
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "hashed_password": target_user.hashed_password,
            "role": target_user.role,
            "phone_number": target_user.phone_number,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user_verification: UserVerification,
    user: JwtUser = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed."
        )

    db_user = db_session.execute(
        select(Users).where(Users.id == user.user_id)
    ).scalar_one_or_none()

    if not verify_password(
        submitted_password=user_verification.password,
        password_hash=db_user.hashed_password,  # type: ignore
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password."
        )
    else:
        db_user.hashed_password = hash_password(user_verification.new_password)  # type: ignore
        try:
            db_session.add(db_user)
            db_session.commit()
            db_session.refresh(db_user)

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


@router.put("/phone-number", status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(
    phone_change: PhoneChange,
    user: JwtUser = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed."
        )

    db_user = db_session.execute(
        select(Users).where(Users.id == user.user_id)
    ).scalar_one_or_none()

    if not verify_password(
        submitted_password=phone_change.password,
        password_hash=db_user.hashed_password,  # type: ignore
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Error on password change"
        )
    else:
        db_user.phone_number = phone_change.new_phone_number  # type: ignore
        try:
            db_session.add(db_user)
            db_session.commit()
            db_session.refresh(db_user)

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
