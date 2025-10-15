from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from datetime import timedelta


from ..request_response_schemas import Token
from ..database import get_db
from ..models import Users
from ..utils.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# Router
router = APIRouter(prefix="/api", tags=["Auth"])


# Endpoints
@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: Session = Depends(get_db),
):
    user: None | Users = authenticate_user(
        username=form_data.username, password=form_data.password, db_session=db_session
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    else:
        access_token = create_access_token(
            username=form_data.username,
            user_id=user.id,  # type: ignore
            role=user.role,  # type: ignore
        )

        refresh_token = create_refresh_token(
            username=form_data.username,
            user_id=user.id,  # type: ignore
            role=user.role,  # type: ignore
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )

        response = JSONResponse(content={"message": "Login successful"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return response


@router.post("/refresh")
async def refresh_access_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token.")

    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    # Issue new access token
    access_token = create_access_token(
        username=payload["username"], user_id=payload["user_id"], role=payload["role"]
    )

    response = JSONResponse(content={"message": "Access token refreshed."})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return response
