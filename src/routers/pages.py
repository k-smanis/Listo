from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/ui", tags=["Login"])

PAGES_DIR = Path(r"D:/portfolio/Listo/app/frontend")
LOGIN_FILE_PATH = PAGES_DIR / "login.html"
TASKS_FILE_PATH = PAGES_DIR / "tasks.html"
ACCOUNT_FILE_PATH = PAGES_DIR / "account.html"
SIGNUP_FILE_PATH = PAGES_DIR / "signup.html"


@router.get("/login")
async def serve_login_page():
    if not LOGIN_FILE_PATH.exists():
        raise HTTPException(404, "login.html not found")
    return FileResponse(LOGIN_FILE_PATH, media_type="text/html")


@router.get("/tasks")
async def serve_tasks_page():
    if not TASKS_FILE_PATH.exists():
        raise HTTPException(404, "tasks.html not found")
    return FileResponse(TASKS_FILE_PATH, media_type="text/html")


@router.get("/account")
async def serve_account_page():
    if not ACCOUNT_FILE_PATH.exists():
        raise HTTPException(404, "account.html not found")
    return FileResponse(ACCOUNT_FILE_PATH, media_type="text/html")


@router.get("/signup")
async def serve_signup_page():
    if not SIGNUP_FILE_PATH.exists():
        raise HTTPException(404, "signup.html not found")
    return FileResponse(SIGNUP_FILE_PATH, media_type="text/html")
