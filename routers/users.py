from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
from routers.auth import AuthUtils

import models
from database import get_db
from request_response_schemas import UserVerification
from routers.auth import JwtUser
from security import hash_password, verify_password

# Initialize Router
router = APIRouter(prefix="/api", tags=["Users"])


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_user(
    user: JwtUser = Depends(AuthUtils.get_current_user),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    return db_session.execute(
        select(models.Users).where(models.Users.id == user.user_id)
    ).scalar_one_or_none()


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user_verification: UserVerification,
    user: JwtUser = Depends(AuthUtils.get_current_user),
    db_session: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed."
        )

    db_user = db_session.execute(
        select(models.Users).where(models.Users.id == user.user_id)
    ).scalar_one_or_none()

    if not verify_password(
        submitted_password=user_verification.password,
        password_hash=db_user.hashed_password,  # type: ignore
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Error on password change"
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
