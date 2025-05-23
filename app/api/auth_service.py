from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
import secrets
import logging

from app.models.auth import TokenData
from app.db.crud import get_document, list_documents
from app.config import settings
import os

# Configure logging
logger = logging.getLogger(__name__)

# Recupera le variabili di ambiente o utilizza valori predefiniti
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

def verify_password(plain_password, hashed_password):
    """Verify if a plain password matches the hashed version"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password for storage"""
    return pwd_context.hash(password)

async def authenticate_user(email: str, password: str):
    """Authenticate a user with email/username and password"""
    users = await list_documents("users", {"email": email})
    
    if not users or len(users) == 0:
        logger.warning(f"No user found with email: {email}")
        return False
    
    user = users[0]
    
    if not user.get("hashed_password"):
        logger.warning(f"User {email} has no password set")
        return False
        
    if not verify_password(password, user.get("hashed_password")):
        logger.warning(f"Invalid password for user {email}")
        return False
    
    # Ensure user has an id field
    if "id" not in user and "_id" in user:
        user["id"] = user["_id"]
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def generate_api_key():
    """Generate a secure API key for device authentication"""
    return secrets.token_urlsafe(32)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        # Find the user in the database
        user = await get_document("users", user_id)
        
        if user is None:
            raise credentials_exception
        
        return user
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Check if the current user is active"""
    if current_user.get("disabled", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user 