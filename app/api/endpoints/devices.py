# app/api/endpoints/devices.py
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from app.models.device import Device
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.services.digital_twin_service import create_digital_twin_for_device
router = APIRouter()

@router.post("/", response_model=Device, status_code=201)
async def create_device(device: Device):
    """Crea un nuovo dispositivo e il suo digital twin"""
    # Salva il dispositivo nel database
    device_dict = device.dict()
    device_id = await create_document("devices", device_dict)
    
    # Ottieni il documento completo del dispositivo salvato
    saved_device = await get_document("devices", device.id)
    
    # Crea un digital twin per questo dispositivo
    digital_twin = await create_digital_twin_for_device(saved_device)
    
    # Aggiorna il dispositivo con l'ID del digital twin
    await update_document("devices", device.id, {"digital_twin_id": digital_twin.id})
    
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
async def update_device(device_id: str, device_update: Device = Body(...)):
    """Aggiorna un dispositivo esistente"""
    existing_device = await get_document("devices", device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
        
    update_data = device_update.dict(exclude_unset=True)
    await update_document("devices", device_id, update_data)
    
    updated_device = await get_document("devices", device_id)
    return updated_device

@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: str):
    """Elimina un dispositivo e il suo digital twin"""
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
        
    # Se esiste un digital twin associato, eliminalo
    if device.get("digital_twin_id"):
        await delete_document("digital_twins", device["digital_twin_id"])
        
    # Elimina il dispositivo
    await delete_document("devices", device_id)
    return None