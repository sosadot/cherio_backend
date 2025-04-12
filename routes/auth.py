from fastapi import APIRouter, HTTPException, Form, Request
import uuid
import bcrypt
from datetime import datetime
from db import get_db

router = APIRouter()


def hash_password(password: str):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")
def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_sso():
    return f"Sso-{uuid.uuid4()}"


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

    # Check if user or email already exists
    cursor.execute("SELECT id FROM users WHERE username = %s OR mail = %s", (username, mail))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed_pw = hash_password(password)
    account_created = int(datetime.utcnow().timestamp())
    ip = request.client.host

    # Insert new user
    cursor.execute("""
        INSERT INTO users (
            username, password, mail, look, gender, motto, `rank`, credits, pixels, points,
            auth_ticket, account_created, last_online, ip_register, ip_current
        )
        VALUES (%s, %s, %s, %s, %s, 'I Love Aland!', 1, 5000, 0, 0, '', %s, 0, %s, %s)
    """, (username, hashed_pw, mail, look, gender, account_created, ip, ip))

    db.commit()

    # Fetch user id
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    jwt_token = create_access_token({"sub": user["id"]}, remember_me=remember_me)

    return {
        "message": f"User '{username}' registered successfully",
        "access_token": jwt_token,
        "token_type": "bearer",
        "username": username
    }


@router.post("/login")
def login_user(username: str = Form(...), password: str = Form(...)):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=403, detail="Invalid username or password")

    jwt_token = create_access_token({"sub": user["id"]}, remember_me=remember_me)

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "username": username
    }

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