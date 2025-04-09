from fastapi import APIRouter, HTTPException
from db import get_db

router = APIRouter()

@router.get("/{user_id}")
def get_user(user_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, username, look, motto FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user