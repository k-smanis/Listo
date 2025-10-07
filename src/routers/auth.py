from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from starlette import status


from ..request_response_schemas import Token
from ..database import get_db
from ..models import Users
from ..utils.auth import authenticate_user, create_access_token

# Router
router = APIRouter(prefix="/api", tags=["Auth"])


# Endpoints
@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
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
