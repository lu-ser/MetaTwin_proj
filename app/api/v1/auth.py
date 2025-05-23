from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.token import Token, TokenData
from app.models.user import User, UserCreate, UserUpdate, UserBase
from app.api.v1.users import create_user, get_user_by_email, get_user, update_user
from app.utils.auth import get_password_hash, verify_password
from app.utils.security import create_access_token, get_current_user
from datetime import timedelta
from app.config import settings
from app.db import users_collection
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["auth"])

# Schema per la modifica della password
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# Schema per la risposta utente
class UserResponse(BaseModel):
    id: str
    email: str
    name: str


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Effettua il login e restituisce un token JWT
    """
    # Ottieni l'utente dall'email
    user = await get_user_by_email(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verifica la password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crea il token JWT con un tempo di scadenza di 30 giorni
    access_token_expires = timedelta(days=30)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """
    Registra un nuovo utente
    """
    # Verifica se l'email è già in uso
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata"
        )
    
    # Crea l'utente
    user = await create_user(user_data)
    
    # Converti l'ID MongoDB ObjectId in stringa
    user["id"] = str(user["_id"])
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"]
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Restituisce i dati dell'utente corrente
    """
    # Converti l'ID MongoDB ObjectId in stringa
    current_user["id"] = str(current_user["_id"])
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"]
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserBase,
    current_user: dict = Depends(get_current_user)
):
    """
    Aggiorna il profilo dell'utente corrente
    """
    # Aggiorna solo il nome
    user = await update_user(str(current_user["_id"]), {"name": user_update.name})
    
    # Converti l'ID MongoDB ObjectId in stringa
    user["id"] = str(user["_id"])
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"]
    )


@router.put("/password")
async def update_password(
    password_update: PasswordUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Aggiorna la password dell'utente corrente
    """
    # Verifica la password attuale
    if not verify_password(password_update.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password attuale non corretta"
        )
    
    # Crea l'hash della nuova password
    hashed_password = get_password_hash(password_update.new_password)
    
    # Aggiorna la password
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    return {"message": "Password aggiornata con successo"} 