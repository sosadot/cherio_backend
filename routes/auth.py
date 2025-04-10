from fastapi import APIRouter, HTTPException, Form
import uuid
import bcrypt
from db import get_db
from auth_utils import create_access_token
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

def hash_password(password: str):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

def generate_sso():
    return f"Sso-{uuid.uuid4()}"

@router.post("/register")
def register_user(username: str = Form(...), password: str = Form(...)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Chod already exists")

    hashed_pw = hash_password(password)

    cursor.execute("""
        INSERT INTO users (username, password, look, gender, motto, rank, credits, pixels, vip_points, auth_ticket)
        VALUES (%s, %s, 'hr-100.hd-180.ch-210-66.lg-280-82.sh-290-64', 'M', 'I am new here!', 1, 5000, 0, 0, '')
    """, (username, hashed_pw))
    db.commit()
    return {"message": f"Chod '{username}' registered successfully"}

@router.post("/login")
def login_user(username: str = Form(...), password: str = Form(...), remember_me: bool = Form(False)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=403, detail="Invalid Chod or password")

    ticket = generate_sso()
    cursor.execute("UPDATE users SET auth_ticket = %s WHERE id = %s", (ticket, user["id"]))
    db.commit()

    jwt_token = create_access_token({"sub": user["id"]}, remember_me=remember_me)

    return {
        "sso_ticket": ticket,
        "jwt_token": jwt_token
    }

@router.get("/sso/{username}")
def get_sso(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT auth_ticket FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Chod not found")
    return {"sso_ticket": user["auth_ticket"]}
