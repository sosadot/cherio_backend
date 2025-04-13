import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

# Environment configuration with sensible defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_SECONDS = 3  # short token in seconds
REMEMBER_ME_EXPIRE_DAYS = int(os.getenv("JWT_REMEMBER_ME_DAYS", 5))  # in days

# For extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, remember_me: bool = False):
    to_encode = data.copy()
    print(f"Remember me (utils): {remember_me}")  # Output to console
    expire = datetime.utcnow() + timedelta(
        days=REMEMBER_ME_EXPIRE_DAYS if remember_me else 0,
        seconds=ACCESS_TOKEN_EXPIRE_SECONDS if not remember_me else 0,
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

