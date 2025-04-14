from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import get_db
from routes.auth import verify_password
from routes.auth import hash_password

router = APIRouter()

# ------------------------------
# Models
# ------------------------------

class LookUpdateRequest(BaseModel):
    username: str
    look: str
    gender: str

class SettingsUpdateRequest(BaseModel):
    username: str
    motto: str
    email: str
    current_password: Optional[str] = None
    new_password: Optional[str] = None

# ------------------------------
# Get User by Username
# ------------------------------

@router.get("/username/{username}")
def get_user_by_username(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, username, look, motto, credits, pixels, points, gender, mail
        FROM users
        WHERE username = %s
    """, (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ------------------------------
# Get Friends
# ------------------------------

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
    return cursor.fetchall()

# ------------------------------
# Online Count
# ------------------------------

@router.get("/online-count")
def get_online_user_count():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE online = 2")
    return cursor.fetchone()

# ------------------------------
# Staff Users
# ------------------------------

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

# ------------------------------
# Group Memberships
# ------------------------------

@router.get("/groups/{username}")
def get_user_groups(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute("""
        SELECT g.id, g.name, g.description, g.badge
        FROM guilds_members gm
        JOIN guilds g ON gm.guild_id = g.id
        WHERE gm.user_id = %s
    """, (user["id"],))
    return cursor.fetchall()

# ------------------------------
# Achievements
# ------------------------------

@router.get("/achievements/{username}")
def get_user_achievements(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute("""
        SELECT achievement_name AS name, progress
        FROM users_achievements
        WHERE user_id = %s
        ORDER BY progress DESC
        LIMIT 5
    """, (user["id"],))
    achievements = cursor.fetchall()
    for ach in achievements:
        ach["badgeImageUrl"] = f"https://images.habbo.com/c_images/album1584/ACH_{ach['name']}{ach['progress']}.gif"
    return achievements

# ------------------------------
# Badges
# ------------------------------

@router.get("/badges/{username}")
def get_user_badges(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute("""
        SELECT badge_code
        FROM users_badges
        WHERE user_id = %s
        ORDER BY slot_id DESC
    """, (user["id"],))
    badges = cursor.fetchall()
    for badge in badges:
        badge["imageUrl"] = f"https://images.habbo.com/c_images/album1584/{badge['badge_code']}.gif"
    return badges

# ------------------------------
# Wardrobe
# ------------------------------

@router.get("/wardrobe/{username}")
def get_user_wardrobe(username: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("""
        SELECT slot_id, look, gender
        FROM users_wardrobe
        WHERE user_id = %s
        ORDER BY slot_id
    """, (user["id"],))

    wardrobe = cursor.fetchall()
    if not wardrobe:
        return []  # Frontend should display "no looks" message
    return wardrobe

# ------------------------------
# Look Update
# ------------------------------

@router.post("/look/update")
def update_user_look(data: LookUpdateRequest):
    print("📥 LOOK PAYLOAD:", data.dict())
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (data.username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute("""
        UPDATE users SET look = %s, gender = %s WHERE id = %s
    """, (data.look, data.gender.upper(), user["id"]))
    db.commit()
    return {"message": "Look updated successfully"}

# ------------------------------
# Settings Update
# ------------------------------

@router.post("/settings/update")
def update_user_settings(data: SettingsUpdateRequest):
    print("📥 SETTINGS PAYLOAD:", data.dict())
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, motto, mail, password FROM users WHERE username = %s", (data.username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["id"]

    if data.motto and data.motto != user["motto"]:
        cursor.execute("UPDATE users SET motto = %s WHERE id = %s", (data.motto, user_id))

    if data.email and data.email != user["mail"]:
        cursor.execute("UPDATE users SET mail = %s WHERE id = %s", (data.email, user_id))

    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to change password")

        if not verify_password(data.current_password, user["password"]):
            raise HTTPException(status_code=403, detail="Current password is incorrect")

        hashed_new = hash_password(data.new_password)
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_new, user_id))

    db.commit()
    return {"message": "Settings updated successfully"}

@router.get("/leaderboard")
def get_leaderboards():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    leaderboards = {}

    # List of all stat categories
    categories = [
        ("credits", "users"),
        ("pixels", "users"),
        ("points", "users"),
        ("respects_received", "users_settings"),
        ("respects_given", "users_settings"),
        ("achievement_score", "users_settings"),
        ("online_time", "users_settings"),
        ("login_streak", "users_settings"),
    ]

    for column, table in categories:
        # Join settings with users if needed
        if table == "users_settings":
            cursor.execute(f"""
                SELECT u.username, u.look, u.gender, s.{column}
                FROM {table} s
                JOIN users u ON u.id = s.user_id
                ORDER BY s.{column} DESC
                LIMIT 10
            """)
        else:
            cursor.execute(f"""
                SELECT username, look, gender, {column}
                FROM {table}
                ORDER BY {column} DESC
                LIMIT 10
            """)

        leaderboards[column] = cursor.fetchall()

    return leaderboards
