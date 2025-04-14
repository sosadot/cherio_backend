from fastapi import APIRouter, HTTPException, Form, Request, status, Depends
from pydantic import BaseModel
import uuid
import bcrypt
from datetime import datetime
from db import get_db
from utils.auth_utils import create_access_token
from response_codes import UserResponseCode

router = APIRouter()

# ------------------------------
# Utility functions
# ------------------------------

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

def generate_sso() -> str:
    return f"cherio-{uuid.uuid4()}"

# ------------------------------
# Pydantic Models
# ------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    username: str
    password: str
    mail: str
    look: str
    gender: str
    remember_me: bool = False

# ------------------------------
# Register (still uses Form)
# ------------------------------

@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    mail: str = Form(...),
    look: str = Form(...),
    gender: str = Form(...),
    remember_me: bool = Form(False),
):
    db = None
    cursor = None
    _ = getattr(request.state, 'gettext', lambda text: text)
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR mail = %s", (username, mail)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": UserResponseCode.REGISTER_TAKEN.value,
                    "message": _("Username or email already exists")
                }
            )

        hashed_pw = hash_password(password)
        account_created = int(datetime.utcnow().timestamp())
        ip = request.client.host

        cursor.execute("""
            INSERT INTO users (
                username, password, mail, look, gender, motto, `rank`, credits, pixels, points,
                auth_ticket, account_created, last_online, ip_register, ip_current
            )
            VALUES (%s, %s, %s, %s, %s, 'I Love Aland!', 1, 5000, 0, 0, '', %s, 0, %s, %s)
        """, (username, hashed_pw, mail, look, gender, account_created, ip, ip))

        db.commit()
        user_id = cursor.lastrowid

        jwt_token = create_access_token({"sub": user_id}, remember_me=remember_me)

        return {
            "message": f"User '{username}' registered successfully",
            "access_token": jwt_token,
            "token_type": "bearer",
            "username": username,
            "user_id": user_id
        }
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()


# ------------------------------
# Login (now accepts JSON ✅)
# ------------------------------

@router.post("/login")
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
):
    db = None
    cursor = None
    _ = getattr(request.state, 'gettext', lambda text: text)

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user or not verify_password(password, user.get("password")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": UserResponseCode.LOGIN_FAILED.value,
                    "message": _("Data combination was not found")
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        jwt_token = create_access_token({"sub": user['id']}, remember_me=remember_me)

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "username": user["username"],
            "user_id": user["id"]
        }
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()


@router.get("/sso/{username}")
async def get_sso(
    request: Request,
    username: str,
):
    db = None
    cursor = None
    _ = getattr(request.state, 'gettext', lambda text: text)
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": UserResponseCode.USER_NOT_FOUND.value,
                    "message": _("User not found")
                }
            )

        ticket = generate_sso()

        cursor.execute("UPDATE users SET auth_ticket = %s WHERE id = %s", (ticket, user["id"]))
        db.commit()

        return {"sso_ticket": ticket}
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
