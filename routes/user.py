from fastapi import APIRouter, HTTPException
from db import get_db

router = APIRouter()

@router.get("/username/{username}")
def get_user_by_username(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, username, look, motto, credits, pixels, points, gender
        FROM users
        WHERE username = %s
    """, (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/friends/{username}")
def get_friends(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user["id"]

    cursor.execute("""
        SELECT u.username, u.look, u.gender, u.online, u.motto
        FROM messenger_friendships mf
        JOIN users u ON (
            (mf.user_one_id = %s AND u.id = mf.user_two_id) OR
            (mf.user_two_id = %s AND u.id = mf.user_one_id)
        )
    """, (user_id, user_id))

    friends = cursor.fetchall()
    return friends


@router.get("/online-count")
def get_online_user_count():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE online = 2")
    result = cursor.fetchone()
    return {"count": result["count"]}


@router.get("/staff")
def get_staff_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, username, look, motto, gender, `rank`
        FROM users
        WHERE `rank` BETWEEN 4 AND 7
        ORDER BY `rank` DESC
    """)
    users = cursor.fetchall()
    if not users:
        raise HTTPException(status_code=404, detail="No staff users found")

    grouped = {
        "Founder": [],
        "Administrator": [],
        "Moderator": [],
        "Event Manager": []
    }

    for user in users:
        if user['rank'] == 7:
            grouped["Founder"].append(user)
        elif user['rank'] == 6:
            grouped["Administrator"].append(user)
        elif user['rank'] == 5:
            grouped["Moderator"].append(user)
        elif user['rank'] == 4:
            grouped["Event Manager"].append(user)

    return grouped