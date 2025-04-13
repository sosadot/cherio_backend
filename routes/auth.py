from fastapi import APIRouter, HTTPException, Form, Request, status
import uuid
import bcrypt
from datetime import datetime
import mysql.connector

from db import get_db
from utils.auth_utils import create_access_token
from response_codes import UserResponseCode

router = APIRouter()

# --- Helper Functions ---

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str | bytes | None) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode("utf-8")
        elif isinstance(hashed_password, bytes):
            hashed_password_bytes = hashed_password
        else:
            return False

        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password_bytes
        )
    except ValueError as ve:
        print(f"ERROR: ValueError during password verification (likely invalid hash format): {ve}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected exception during password verification: {e}")
        return False

def generate_sso() -> str:
    return f"Sso-{uuid.uuid4()}"

# --- End Helper Functions ---


# --- Routes ---

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
    try:
        _ = request.state.gettext

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
        ip = request.client.host if request.client else "unknown"

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
    except mysql.connector.Error as db_err:
        print(f"Database error during registration: {db_err}")
        message = "An unexpected database error occurred."
        try:
            message = request.state.gettext("An unexpected database error occurred.")
        except AttributeError:
            print("Warning: request.state.gettext not available in DB error handler (register).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "code": UserResponseCode.GENERIC_ERROR.value, "message": message }
        )
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        print(f"Unexpected error during registration: {e}")
        message = "An unexpected error occurred."
        try:
            message = request.state.gettext("An unexpected error occurred.")
        except AttributeError:
            print("Warning: request.state.gettext not available in generic error handler (register).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "code": UserResponseCode.GENERIC_ERROR.value, "message": message }
        )
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()


@router.post("/login")
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
):
    db = None
    cursor = None
    try:
        _ = request.state.gettext

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        password_matches = False
        if user:
            db_password = user.get("password")
            password_matches = verify_password(password, db_password)

        if not user or not password_matches:
            message = _("Data combination was not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={ "code": UserResponseCode.LOGIN_FAILED.value, "message": message },
                headers={"WWW-Authenticate": "Bearer"},
            )

        jwt_token = create_access_token({"sub": user['id']}, remember_me=remember_me)

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "username": user["username"],
            "user_id": user["id"]
        }
    except mysql.connector.Error as db_err:
        print(f"Database error during login: {db_err}")
        message = "An unexpected database error occurred."
        try:
            message = request.state.gettext("An unexpected database error occurred.")
        except AttributeError:
            print("Warning: request.state.gettext not available in DB error handler (login).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "code": UserResponseCode.GENERIC_ERROR.value, "message": message }
        )
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        print(f"Unexpected error during login: {e}")
        message = "An unexpected error occurred."
        try:
            message = request.state.gettext("An unexpected error occurred.")
        except AttributeError:
            print("Warning: request.state.gettext not available in generic error handler (login).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "code": UserResponseCode.GENERIC_ERROR.value, "message": message }
        )
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
    try:
        _ = request.state.gettext

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
    except mysql.connector.Error as db_err:
        print(f"Database error during SSO generation: {db_err}")
        message = "An unexpected database error occurred."
        try:
            message = request.state.gettext("An unexpected database error occurred.")
        except AttributeError:
            print("Warning: request.state.gettext not available in DB error handler (sso).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "code": UserResponseCode.GENERIC_ERROR.value, "message": message }
        )
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        print(f"Unexpected error during SSO generation: {e}")
        message = "An unexpected error occurred."
        try:
            message = request.state.gettext("An unexpected error occurred.")
        except AttributeError:
            print("Warning: request.state.gettext not available in generic error handler (sso).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "code": UserResponseCode.GENERIC_ERROR.value, "message": message }
        )
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
