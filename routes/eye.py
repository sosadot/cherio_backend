from fastapi import APIRouter, Request, HTTPException, Depends, Body
from db import get_db_session
from datetime import datetime
import traceback

router = APIRouter()


@router.get("/")
async def access_eye_panel(request: Request, db_session=Depends(get_db_session)):
    try:
        db, cursor = db_session

        client_ip = request.client.host
        username = request.headers.get("X-Username")

        print(f"👁️ Attempted Eye access — IP: {client_ip}, Username: {username}")

        # Always log access attempt
        cursor.execute("""
            INSERT INTO access_logs (username, ip, accessed_at, route)
            VALUES (%s, %s, %s, %s)
        """, (username if username else "unauthenticated", client_ip, datetime.utcnow(), "/eye"))
        db.commit()

        if not username:
            return {
                "error": "Unauthorized access",
                "message": f"👁️ Your IP {client_ip} has been logged for trying to access The Eye without logging in."
            }

        # Check user rank
        cursor.execute("SELECT username, `rank` FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user or user["rank"] < 6:
            print(f"❌ Unauthorized user '{username}' (Rank: {user['rank'] if user else 'Unknown'}) tried to access The Eye")
            return {
                "error": "Unauthorized access",
                "message": f"👁️ Your IP {client_ip} has been logged for trying to access The Eye without permission."
            }

        # Authorized access
        print(f"✅ Authorized access by {username} (Rank: {user['rank']})")
        return {
            "message": "👁️ Welcome to The Eye",
            "username": user["username"],
            "rank": user["rank"]
        }

    except Exception as e:
        print("🔥 ERROR in /eye route:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users")
async def get_all_users(request: Request, db_session=Depends(get_db_session)):
    try:
        db, cursor = db_session
        client_ip = request.client.host
        username = request.headers.get("X-Username")

        print(f"👁️ Fetching /eye/users — IP: {client_ip}, Username: {username}")

        if not username:
            return {
                "error": True,
                "message": f"👁️ Your IP {client_ip} has been logged for trying to access The Eye without logging in."
            }

        # ✅ Ensure this is correct
        cursor.execute("SELECT username, `rank` FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        print("👤 User from DB:", user)

        if not user or user["rank"] < 6:
            print(f"❌ Unauthorized user '{username}' (Rank: {user['rank'] if user else 'Unknown'}) tried to access /eye/users")
            return {
                "error": True,
                "message": f"👁️ Your IP {client_ip} has been logged for trying to access The Eye without permission."
            }

        # ✅ Main query
        cursor.execute("SELECT id, username, motto, `rank` FROM users ORDER BY id ASC")
        users = cursor.fetchall()

        return {
            "error": False,
            "users": users
        }

    except Exception as e:
        import traceback
        print("🔥 ERROR in /eye/users:", e)
        traceback.print_exc()
        return {
            "error": True,
            "message": "Internal server error while fetching users."
        }

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int, request: Request, db_session=Depends(get_db_session)):
    db, cursor = db_session
    username = request.headers.get("X-Username")
    client_ip = request.client.host

    print(f"👁️ /eye/users/{user_id} access by: {username} from {client_ip}")

    # Log attempt
    cursor.execute("""
        INSERT INTO access_logs (username, ip, accessed_at, route)
        VALUES (%s, %s, %s, %s)
    """, (username or "unauthenticated", client_ip, datetime.utcnow(), f"/eye/users/{user_id}"))
    db.commit()

    # Check permissions
    if not username:
        return {
            "error": True,
            "message": f"👁️ Your IP {client_ip} has been logged for trying to access The Eye without logging in."
        }

    cursor.execute("SELECT `rank` FROM users WHERE username = %s", (username,))
    user_check = cursor.fetchone()

    if not user_check or user_check["rank"] < 6:
        return {
            "error": True,
            "message": f"👁️ Your IP {client_ip} has been logged for trying to access The Eye without permission."
        }

    # Fetch user
    cursor.execute("""
    SELECT id, username, motto, mail, look, gender, `rank`, credits, pixels, points
    FROM users WHERE id = %s
""", (user_id,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user": user
    }

@router.post("/users/{user_id}/update")
async def update_user(user_id: int, request: Request, db_session=Depends(get_db_session)):
    db, cursor = db_session

    try:
        data = await request.json()
        username = request.headers.get("X-Username")
        client_ip = request.client.host

        print(f"👁️ /eye/users/{user_id}/update by: {username} from {client_ip}")
        
        # Optional: Log access
        cursor.execute("""
            INSERT INTO access_logs (username, ip, accessed_at, route)
            VALUES (%s, %s, %s, %s)
        """, (username or "unauthenticated", client_ip, datetime.utcnow(), f"/eye/users/{user_id}/update"))

        # Optional: Verify updater's permissions
        cursor.execute("SELECT `rank` FROM users WHERE username = %s", (username,))
        updater = cursor.fetchone()
        if not updater or updater["rank"] < 6:
            return {
                "error": True,
                "message": f"👁️ Unauthorized: You do not have permission to update users."
            }

        fields = ["motto", "mail", "credits", "pixels", "points", "rank"]
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f"`{field}` = %s")
                values.append(data[field])

        if not updates:
            return { "message": "No changes submitted." }

        values.append(user_id)
        update_query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"

        print("🛠️ Running update:", update_query)
        print("📦 Values:", values)

        cursor.execute(update_query, tuple(values))
        db.commit()

        return { "message": "✅ User updated successfully." }

    except Exception as e:
        print("🔥 Error updating user:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to update user.")