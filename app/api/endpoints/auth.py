from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.auth import Token, UserCreate, UserLogin
from app.models.user import User
from app.api.auth_service import (
    authenticate_user, 
    create_access_token,
    get_current_active_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.db.crud import create_document, list_documents

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Restituisce un token di accesso JWT se le credenziali sono valide"""
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User, status_code=201)
async def register_user(user_data: UserCreate):
    """Registra un nuovo utente"""
    # Controlla se l'email è già in uso
    existing_users = await list_documents("users", {"email": user_data.email})
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già in uso"
        )
    
    # Crea un nuovo utente
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name, 
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    user_dict = user.dict()
    await create_document("users", user_dict)
    
    # Rimuovi l'hash della password dalla risposta
    user_dict.pop("hashed_password", None)
    
    return user_dict

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Effettua il login utilizzando email e password"""
    user = await authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user = Depends(get_current_active_user)):
    """Restituisce le informazioni dell'utente attualmente autenticato"""
    # Rimuovi l'hash della password dalla risposta
    user_dict = current_user.copy()
    user_dict.pop("hashed_password", None)
    
    return user_dict 