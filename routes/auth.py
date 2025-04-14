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

def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed_password.encode("utf-8")
    )

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
# Register (now uses JSON)
# ------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    register_data: RegisterRequest
):
    db = None
    cursor = None
    _ = getattr(request.state, 'gettext', lambda text: text)
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR mail = %s",
            (register_data.username, register_data.mail)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": UserResponseCode.REGISTER_TAKEN.value,
                    "message": _("Username or email already exists")
                }
            )

        hashed_pw = hash_password(register_data.password)
        account_created = int(datetime.utcnow().timestamp())
        ip = request.client.host if request.client else "unknown"

        cursor.execute("""
            INSERT INTO users (
                username, password, mail, look, gender, motto, `rank`, credits, pixels, points,
                auth_ticket, account_created, last_online, ip_register, ip_current
            )
            VALUES (%s, %s, %s, %s, %s, 'I Love Aland!', 1, 5000, 0, 0, '', %s, 0, %s, %s)
        """, (
            register_data.username,
            hashed_pw,
            register_data.mail,
            register_data.look,
            register_data.gender,
            account_created,
            ip,
            ip
        ))

        db.commit()
        user_id = cursor.lastrowid

        jwt_token = create_access_token(
            {"sub": user_id},
            remember_me=register_data.remember_me
        )

        return {
            "message": _("User '{username}' registered successfully").format(
                username=register_data.username
            ),
            "jwt_token": jwt_token,
            "token_type": "bearer",
            "username": register_data.username,
            "user_id": user_id
        }
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": UserResponseCode.REGISTRATION_FAILED.value,
                "message": _("Registration failed due to an internal error.")
            }
        ) from e
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
    login_data: LoginRequest
):
    db = None
    cursor = None
    _ = getattr(request.state, 'gettext', lambda text: text)

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (login_data.username,))
        user = cursor.fetchone()

        if not user or not verify_password(login_data.password, user.get("password")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": UserResponseCode.LOGIN_FAILED.value,
                    "message": _("Data combination was not found")
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        jwt_token = create_access_token({"sub": user['id']}, remember_me=login_data.remember_me)

        # ip = request.client.host if request.client else "unknown"
        # cursor.execute("UPDATE users SET last_online = %s, ip_current = %s WHERE id = %s",
        #                (int(datetime.utcnow().timestamp()), ip, user['id']))
        # db.commit()

        return {
            "jwt_token": jwt_token,
            "token_type": "bearer",
            "username": user["username"],
            "user_id": user["id"]
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": UserResponseCode.LOGIN_ERROR.value,
                "message": _("Login failed due to an internal error.")
            }
        ) from e
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
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": UserResponseCode.SSO_ERROR.value,
                "message": _("SSO ticket generation failed.")
            }
        ) from e
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
