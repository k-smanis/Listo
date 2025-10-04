from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status


from ..request_response_schemas import CreateUser, Token
from ..database import get_db
from ..models import Users
from ..utils.security import hash_password
from ..utils.auth import authenticate_user, create_access_token

# Intialize Router
router = APIRouter(prefix="/api", tags=["Auth"])


# TODO: Move this endpoint to users.py
@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    create_user_request: CreateUser = Body(...), db_session: Session = Depends(get_db)
):
    new_user = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name.capitalize(),
        last_name=create_user_request.last_name.capitalize(),
        role=create_user_request.role,
        hashed_password=hash_password(create_user_request.password),
        is_active=True,
        phone_number=create_user_request.phone_number,
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
    user: None | Users = authenticate_user(
        username=form_data.username, password=form_data.password, db_session=db_session
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )
    else:
        token = create_access_token(
            username=form_data.username, user_id=user.id, role=user.role  # type: ignore
        )
        return {"access_token": token, "token_type": "bearer"}
