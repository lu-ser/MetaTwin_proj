# app/api/endpoints/devices.py
from fastapi import APIRouter, HTTPException, Body, Depends, Header, Query
from typing import List, Optional, Dict, Any
from app.models.device import Device
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.services.digital_twin_service import create_digital_twin_for_device
from app.api.auth import get_device_by_api_key, verify_device_ownership
import secrets

router = APIRouter()

@router.post("/", response_model=Device, status_code=201)
async def create_device(device: Device, regenerate_api_key: bool = Query(False)):
    """
    Crea un nuovo dispositivo e il suo digital twin
    
    Se specificato owner_id, aggiorna anche l'utente collegando il dispositivo
    """
    # Se è richiesto di rigenerare API key o non è presente
    if regenerate_api_key or not device.api_key:
        device.api_key = secrets.token_urlsafe(32)
    
    # Salva il dispositivo nel database
    device_dict = device.dict()
    device_id = await create_document("devices", device_dict)
    
    # Ottieni il documento completo del dispositivo salvato
    saved_device = await get_document("devices", device.id)
    
    # Crea un digital twin per questo dispositivo
    digital_twin = await create_digital_twin_for_device(saved_device)
    
    # Aggiorna il dispositivo con l'ID del digital twin
    await update_document("devices", device.id, {"digital_twin_id": digital_twin.id})
    
    # Se è specificato un proprietario, aggiorna anche l'utente
    if device.owner_id:
        user = await get_document("users", device.owner_id)
        if user:
            # Aggiungi l'ID del dispositivo alla lista dei dispositivi dell'utente
            user_devices = user.get("devices", [])
            if device.id not in user_devices:
                user_devices.append(device.id)
                await update_document("users", device.owner_id, {"devices": user_devices})
                
            # Aggiungi anche il digital twin
            user_digital_twins = user.get("digital_twins", [])
            if digital_twin.id not in user_digital_twins:
                user_digital_twins.append(digital_twin.id)
                await update_document("users", device.owner_id, {"digital_twins": user_digital_twins})
    
    # Recupera il dispositivo aggiornato
    updated_device = await get_document("devices", device.id)
    return updated_device

@router.get("/", response_model=List[Device])
async def list_devices(owner_id: Optional[str] = None):
    """Ottieni tutti i dispositivi, opzionalmente filtrando per proprietario"""
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
        
    devices = await list_documents("devices", query)
    return devices

@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str):
    """Ottieni un dispositivo specifico tramite ID"""
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return device

@router.put("/{device_id}", response_model=Device)
async def update_device(
    device_id: str, 
    device_update: Device = Body(...),
    regenerate_api_key: bool = Query(False)
):
    """
    Aggiorna un dispositivo esistente
    
    Se cambia owner_id, aggiorna anche i modelli utente coinvolti
    """
    existing_device = await get_document("devices", device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Prepara i dati dell'aggiornamento
    update_data = device_update.dict(exclude_unset=True)
    
    # Gestione del cambio di proprietario
    old_owner_id = existing_device.get("owner_id")
    new_owner_id = device_update.owner_id
    
    # Se è richiesto di rigenerare API key
    if regenerate_api_key:
        update_data["api_key"] = secrets.token_urlsafe(32)
    
    # Aggiorna il dispositivo
    await update_document("devices", device_id, update_data)
    updated_device = await get_document("devices", device_id)
    
    # Se il proprietario è cambiato, aggiorna entrambi gli utenti
    if new_owner_id != old_owner_id:
        # Rimuovi il dispositivo dal vecchio proprietario
        if old_owner_id:
            old_owner = await get_document("users", old_owner_id)
            if old_owner:
                # Rimuovi dispositivo
                old_devices = old_owner.get("devices", [])
                if device_id in old_devices:
                    old_devices.remove(device_id)
                    await update_document("users", old_owner_id, {"devices": old_devices})
                
                # Rimuovi digital twin
                digital_twin_id = existing_device.get("digital_twin_id")
                if digital_twin_id:
                    old_digital_twins = old_owner.get("digital_twins", [])
                    if digital_twin_id in old_digital_twins:
                        old_digital_twins.remove(digital_twin_id)
                        await update_document("users", old_owner_id, {"digital_twins": old_digital_twins})
        
        # Aggiungi il dispositivo al nuovo proprietario
        if new_owner_id:
            new_owner = await get_document("users", new_owner_id)
            if new_owner:
                # Aggiungi dispositivo
                new_devices = new_owner.get("devices", [])
                if device_id not in new_devices:
                    new_devices.append(device_id)
                    await update_document("users", new_owner_id, {"devices": new_devices})
                
                # Aggiungi digital twin
                digital_twin_id = updated_device.get("digital_twin_id")
                if digital_twin_id:
                    new_digital_twins = new_owner.get("digital_twins", [])
                    if digital_twin_id not in new_digital_twins:
                        new_digital_twins.append(digital_twin_id)
                        await update_document("users", new_owner_id, {"digital_twins": new_digital_twins})
    
    return updated_device

@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: str):
    """
    Elimina un dispositivo e il suo digital twin
    
    Aggiorna anche l'utente proprietario rimuovendo i riferimenti
    """
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Rimuovi il dispositivo dall'utente se è collegato
    owner_id = device.get("owner_id")
    if owner_id:
        owner = await get_document("users", owner_id)
        if owner:
            # Rimuovi dispositivo
            owner_devices = owner.get("devices", [])
            if device_id in owner_devices:
                owner_devices.remove(device_id)
                await update_document("users", owner_id, {"devices": owner_devices})
            
            # Rimuovi digital twin
            digital_twin_id = device.get("digital_twin_id")
            if digital_twin_id:
                owner_digital_twins = owner.get("digital_twins", [])
                if digital_twin_id in owner_digital_twins:
                    owner_digital_twins.remove(digital_twin_id)
                    await update_document("users", owner_id, {"digital_twins": owner_digital_twins})
        
    # Se esiste un digital twin associato, eliminalo
    if device.get("digital_twin_id"):
        await delete_document("digital_twins", device["digital_twin_id"])
        
    # Elimina il dispositivo
    await delete_document("devices", device_id)
    return None

@router.post("/auth/verify", response_model=Device)
async def verify_device(device: Device = Depends(get_device_by_api_key)):
    """
    Verifica l'autenticazione di un dispositivo tramite API key
    
    Restituisce il dispositivo se l'autenticazione ha successo
    """
    return device

@router.post("/regenerate-api-key", response_model=Dict[str, str])
async def regenerate_api_key(device_id: str):
    """
    Rigenera l'API key per un dispositivo
    
    Restituisce la nuova API key generata
    """
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Genera una nuova API key
    new_api_key = secrets.token_urlsafe(32)
    
    # Aggiorna il dispositivo
    await update_document("devices", device_id, {"api_key": new_api_key})
    
    return {"api_key": new_api_key}