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

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

