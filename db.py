import mysql.connector
import os
from fastapi import HTTPException, status

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "your_db_user"),
    "password": os.getenv("DB_PASSWORD", "your_db_password"),
    "database": os.getenv("DB_NAME", "your_db_name"),
    "pool_name": "fastapi_pool",
    "pool_size": 5,
}

def _get_raw_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None
    except Exception as e:
        print(f"Unexpected error getting DB connection: {e}")
        return None

async def get_db_session():
    db = None
    cursor = None
    try:
        db = _get_raw_db_connection()
        if db is None or not db.is_connected():
             raise HTTPException(
                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                 detail="Could not connect to the database."
             )
        cursor = db.cursor(dictionary=True)
        yield db, cursor

    except mysql.connector.Error as err:
         print(f"Database operation error within session: {err}")
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Database operation failed."
         )
    finally:
        # This cleanup ALWAYS runs, regardless of exceptions in the route
        if cursor:
            try: cursor.close()
            except: pass
        if db and db.is_connected():
            try: db.close()
            except: pass #

