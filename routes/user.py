from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from db import get_db_session
from utils.auth_utils import verify_password, hash_password
import mysql.connector


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
async def get_user_by_username(
    username: str,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
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
async def get_friends(
    username: str,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
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

# ------------------------------
# Online Count
# ------------------------------

@router.get("/online-count")
async def get_online_user_count(db_session = Depends(get_db_session)): # Use dependency
    db, cursor = db_session # Unpack
    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE online = 2")
    count_result = cursor.fetchone()
    return count_result

# ------------------------------
# Staff Users
# ------------------------------

@router.get("/staff")
async def get_staff_users(db_session = Depends(get_db_session)): # Use dependency
    db, cursor = db_session # Unpack
    cursor.execute("""
        SELECT id, username, look, motto, gender, `rank`
        FROM users
        WHERE `rank` BETWEEN 4 AND 7
        ORDER BY `rank` DESC
    """)
    users = cursor.fetchall()
    if not users:
        # Changed to return empty structure instead of 404, adjust if needed
        return {
            "Founder": [], "Administrator": [], "Moderator": [], "Event Manager": []
        }
        # raise HTTPException(status_code=404, detail="No staff users found")


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
async def get_user_groups(
    username: str,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
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
    groups = cursor.fetchall()
    return groups

# ------------------------------
# Achievements
# ------------------------------

@router.get("/achievements/{username}")
async def get_user_achievements(
    username: str,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
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
async def get_user_badges(
    username: str,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
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
async def get_user_wardrobe(
    username: str,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack

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
    # Returning empty list is fine, no need to check 'if not wardrobe' here
    return wardrobe

# ------------------------------
# Look Update
# ------------------------------

@router.post("/look/update")
async def update_user_look(
    data: LookUpdateRequest,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
    print("📥 LOOK PAYLOAD:", data.dict())

    cursor.execute("SELECT id FROM users WHERE username = %s", (data.username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("""
        UPDATE users SET look = %s, gender = %s WHERE id = %s
    """, (data.look, data.gender.upper(), user["id"]))

    try:
        db.commit() # Commit using yielded db
    except mysql.connector.Error as commit_err:
        print(f"Commit failed during look update: {commit_err}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update look.")

    return {"message": "Look updated successfully"}

# ------------------------------
# Settings Update
# ------------------------------

@router.post("/settings/update")
async def update_user_settings(
    data: SettingsUpdateRequest,
    db_session = Depends(get_db_session) # Use dependency
):
    db, cursor = db_session # Unpack
    print("📥 SETTINGS PAYLOAD:", data.dict())

    cursor.execute("SELECT id, motto, mail, password FROM users WHERE username = %s", (data.username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["id"]
    updated = False # Flag to track if any update happened

    if data.motto and data.motto != user["motto"]:
        cursor.execute("UPDATE users SET motto = %s WHERE id = %s", (data.motto, user_id))
        updated = True

    if data.email and data.email != user["mail"]:
        # Optional: Add email validation here if needed
        cursor.execute("UPDATE users SET mail = %s WHERE id = %s", (data.email, user_id))
        updated = True

    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to change password")

        if not verify_password(data.current_password, user["password"]):
            raise HTTPException(status_code=403, detail="Current password is incorrect")

        hashed_new = hash_password(data.new_password)
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_new, user_id))
        updated = True

    if updated:
        try:
            db.commit() # Commit using yielded db
        except mysql.connector.Error as commit_err:
            print(f"Commit failed during settings update: {commit_err}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save settings.")
    else:
         # Optional: Return a different message if nothing changed
         return {"message": "No settings were changed."}


    return {"message": "Settings updated successfully"}

# Note: Removed duplicate /leaderboard endpoint from user.py, assuming it's in general.py

