import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

# Environment configuration with sensible defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 5))  # short token
REMEMBER_ME_EXPIRE_DAYS = int(os.getenv("JWT_REMEMBER_ME_DAYS", 5)) * 24 * 60  # in minutes

# For extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ---------------------------
# JWT Token Utilities
# ---------------------------

def create_access_token(data: dict, remember_me: bool = False):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=REMEMBER_ME_EXPIRE_DAYS if remember_me else ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

# ---------------------------
# Bcrypt Password Utilities ✅
# ---------------------------

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
