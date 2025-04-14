from fastapi import APIRouter
from db import get_db

router = APIRouter()

@router.get("/leaderboard")
async def get_leaderboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    stats = [
        "credits",
        "pixels",
        "points",
        "respects_received",
        "respects_given",
        "achievement_score",
        "online_time",
        "login_streak"
    ]

    result = {}

    for stat in stats:
        if stat in ["credits", "pixels", "points"]:
            cursor.execute(f"""
                SELECT username, look, gender, {stat}
                FROM users
                ORDER BY {stat} DESC
                LIMIT 10
            """)
        else:
            cursor.execute(f"""
                SELECT u.username, u.look, u.gender, s.{stat}
                FROM users_settings s
                JOIN users u ON u.id = s.user_id
                ORDER BY s.{stat} DESC
                LIMIT 10
            """)
        result[stat] = cursor.fetchall()

    return result