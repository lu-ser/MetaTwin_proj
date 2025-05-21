# app/api/auth.py
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from app.db.crud import list_documents
from typing import Optional, Dict, Any
import logging

# Logger
logger = logging.getLogger(__name__)

# Header per la chiave API
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_device_by_api_key(api_key: str = Security(api_key_header)) -> Optional[Dict[str, Any]]:
    """
    Verifica se una chiave API è valida e recupera il dispositivo associato.
    
    Args:
        api_key: La chiave API da verificare
        
    Returns:
        Device: Il dispositivo associato alla chiave API
        
    Raises:
        HTTPException: Se la chiave API non è valida o non è presente
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key mancante",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Cerca il dispositivo con questa API key
    devices = await list_documents("devices", {"api_key": api_key})
    
    if not devices or len(devices) == 0:
        logger.warning(f"Tentativo di accesso con API key non valida: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="API key non valida",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return devices[0]

async def verify_device_ownership(device_id: str, owner_id: str) -> None:
    """
    Verifica che un dispositivo appartenga a un utente specifico
    
    Args:
        device_id: ID del dispositivo
        owner_id: ID dell'utente proprietario
        
    Raises:
        HTTPException: Se il dispositivo non appartiene all'utente specificato
    """
    devices = await list_documents("devices", {"id": device_id})
    
    if not devices or len(devices) == 0:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    device = devices[0]
    
    if device.get("owner_id") != owner_id:
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per accedere a questo dispositivo"
        )