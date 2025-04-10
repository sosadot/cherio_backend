import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

# Load secret key and algorithm from environment or use defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 30))
REMEMBER_ME_EXPIRE_DAYS = int(os.getenv("JWT_REMEMBER_ME_DAYS", 365))

# For extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, remember_me: bool = False):
    to_encode = data.copy()

    if remember_me:
        expire = datetime.utcnow() + timedelta(days=REMEMBER_ME_EXPIRE_DAYS)
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
