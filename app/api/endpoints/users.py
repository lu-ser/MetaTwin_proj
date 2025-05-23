# app/api/endpoints/users.py
from fastapi import APIRouter, HTTPException, Body, Path, Depends
from typing import List, Dict, Any, Optional

from app.models.user import User
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.api.auth_service import get_current_active_user

router = APIRouter()

@router.post("/", response_model=User, status_code=201)
async def create_user(user: User, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Crea un nuovo utente"""
    # Verifica se esiste già un utente con la stessa email
    if user.email:
        existing_users = await list_documents("users", {"email": user.email})
        if existing_users:
            raise HTTPException(status_code=400, detail="Email già in uso")
    
    # Salva l'utente nel database
    user_dict = user.dict()
    await create_document("users", user_dict)
    
    return user

@router.get("/", response_model=List[User])
async def list_users(name: Optional[str] = None):
    """Ottieni tutti gli utenti, opzionalmente filtrando per nome"""
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive regex
        
    users = await list_documents("users", query)
    return users

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Ottieni un utente specifico tramite ID"""
    user = await get_document("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str, 
    user_update: User = Body(...), 
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Aggiorna un utente esistente"""
    # Verifica se l'utente corrente sta modificando se stesso o ha i privilegi per farlo
    if current_user["id"] != user_id:
        # Qui potresti aggiungere ulteriori controlli per i ruoli, ad esempio admin
        raise HTTPException(status_code=403, detail="Non hai i permessi per modificare questo utente")
    
    existing_user = await get_document("users", user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Verifica se si sta tentando di cambiare email con una già esistente
    if user_update.email and user_update.email != existing_user.get("email"):
        existing_with_email = await list_documents("users", {"email": user_update.email})
        if existing_with_email:
            raise HTTPException(status_code=400, detail="Email già in uso")
    
    # Aggiorna l'utente
    update_data = user_update.dict(exclude_unset=True)
    
    # Assicurati di non sovrascrivere il password hash
    if "hashed_password" in update_data and not update_data["hashed_password"]:
        update_data.pop("hashed_password")
    
    update_result = await update_document("users", user_id, update_data)
    
    if not update_result:
        raise HTTPException(status_code=500, detail="Aggiornamento fallito")
    
    updated_user = await get_document("users", user_id)
    return updated_user

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Elimina un utente"""
    # Verifica se l'utente corrente sta eliminando se stesso o ha i privilegi per farlo
    if current_user["id"] != user_id:
        # Qui potresti aggiungere ulteriori controlli per i ruoli, ad esempio admin
        raise HTTPException(status_code=403, detail="Non hai i permessi per eliminare questo utente")
    
    user = await get_document("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Recupera tutti i dispositivi associati all'utente
    devices = await list_documents("devices", {"owner_id": user_id})
    
    # Per ogni dispositivo, elimina anche il digital twin associato
    for device in devices:
        if "digital_twin_id" in device:
            await delete_document("digital_twins", device["digital_twin_id"])
        await delete_document("devices", device["id"])
    
    # Elimina l'utente
    await delete_document("users", user_id)
    
    return None

@router.get("/{user_id}/devices", response_model=List[Dict[str, Any]])
async def get_user_devices(user_id: str):
    """Ottieni tutti i dispositivi di un utente"""
    user = await get_document("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    devices = await list_documents("devices", {"owner_id": user_id})
    return devices

@router.get("/{user_id}/digital-twins", response_model=List[Dict[str, Any]])
async def get_user_digital_twins(user_id: str):
    """Ottieni tutti i digital twins di un utente"""
    user = await get_document("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    digital_twins = await list_documents("digital_twins", {"owner_id": user_id})
    return digital_twins