# app/api/auth.py
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from app.db.crud import list_documents
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import secrets
from jose import JWTError, jwt
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.models.user import User
from app.config import settings

# Logger
logger = logging.getLogger(__name__)

# Header per la chiave API
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration with token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

# Verify password function
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Hash password function
def get_password_hash(password):
    return pwd_context.hash(password)

# Create access token function
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Generate a secure API key
def generate_api_key():
    return secrets.token_urlsafe(32)

# Get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Find user in database
        user = User.find_by_id(user_id)
        if user is None:
            raise credentials_exception
        
        return user
    except JWTError:
        raise credentials_exception

# Get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Authenticate user
def authenticate_user(email: str, password: str):
    user = User.find_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_device_by_api_key(api_key: str = Security(api_key_header)) -> Optional[Dict[str, Any]]:
    """
    Verifies if an API key is valid and retrieves the associated device.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        Device: The device associated with the API key
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Search for the device with this API key
    devices = await list_documents("devices", {"api_key": api_key})
    
    if not devices or len(devices) == 0:
        logger.warning(f"Attempt to access with invalid API key: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return devices[0]

async def verify_device_ownership(device_id: str, owner_id: str) -> None:
    """
    Verify that a device belongs to a specific user
    
    Args:
        device_id: Device ID
        owner_id: ID of the owner user
        
    Raises:
        HTTPException: If the device doesn't belong to the specified user
    """
    devices = await list_documents("devices", {"id": device_id})
    
    if not devices or len(devices) == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device = devices[0]
    
    if device.get("owner_id") != owner_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to access this device"
        )