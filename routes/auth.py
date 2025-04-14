from fastapi import APIRouter, HTTPException, Request, Form
from pydantic import BaseModel
import uuid
import bcrypt
from datetime import datetime
from db import get_db
from utils.auth_utils import create_access_token

router = APIRouter()

# ------------------------------
# Utility functions
# ------------------------------

def hash_password(password: str):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

def generate_sso():
    return f"Sso-{uuid.uuid4()}"

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
def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    mail: str = Form(...),
    look: str = Form(...),
    gender: str = Form(...),
    remember_me: bool = Form(False)
):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id FROM users WHERE username = %s OR mail = %s", (username, mail))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username or email already exists")

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

    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    jwt_token = create_access_token({"sub": user["id"]}, remember_me=remember_me)

    return {
        "message": f"User '{username}' registered successfully",
        "access_token": jwt_token,
        "token_type": "bearer",
        "username": username
    }

# ------------------------------
# Login (now accepts JSON ✅)
# ------------------------------

@router.post("/login")
def login_user(data: LoginRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, password FROM users WHERE username = %s", (data.username,))
    user = cursor.fetchone()
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=403, detail="Invalid username or password")

    jwt_token = create_access_token({"sub": user["id"]}, remember_me=data.remember_me)

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "username": data.username
    }

# ------------------------------
# SSO Ticket
# ------------------------------

@router.get("/sso/{username}")
def get_sso(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ticket = generate_sso()
    cursor.execute("UPDATE users SET auth_ticket = %s WHERE id = %s", (ticket, user["id"]))
    db.commit()

    return {"sso_ticket": ticket}