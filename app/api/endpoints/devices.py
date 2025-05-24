# app/api/endpoints/devices.py
from fastapi import APIRouter, HTTPException, Body, Depends, Header, Query, Path
from typing import List, Optional, Dict, Any, Union
from app.models.device import Device
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.services.digital_twin_service import create_digital_twin_for_device
from app.api.auth import get_device_by_api_key, verify_device_ownership
from app.api.auth_service import get_current_active_user
import secrets

router = APIRouter()

@router.post("/", response_model=Device, status_code=201)
async def create_device(
    device: Device, 
    regenerate_api_key: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Crea un nuovo dispositivo e il suo digital twin
    
    Il dispositivo può essere basato sull'ontologia (device_type) o su un template (template_id)
    """
    # Se l'owner_id non è specificato, imposta l'utente corrente come proprietario
    if not device.owner_id:
        device.owner_id = current_user["id"]
    
    # Verifica che l'utente corrente possa creare un dispositivo per il proprietario specificato
    if device.owner_id != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per creare dispositivi per altri utenti"
        )
    
    # Verifica che il device abbia o device_type o template_id
    if not device.device_type and not device.template_id:
        raise HTTPException(
            status_code=400,
            detail="È necessario specificare almeno uno tra device_type (ontologia) e template_id (template personalizzato)"
        )
    
    # Se viene fornito template_id, verifica che esista
    if device.template_id:
        template = await get_document("device_templates", device.template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template con ID '{device.template_id}' non trovato"
            )
    
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
async def list_devices(
    owner_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ottieni tutti i dispositivi, opzionalmente filtrando per proprietario"""
    query = {}
    
    # Se viene specificato un owner_id, verifica che l'utente possa vedere questi dispositivi
    if owner_id and owner_id != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        # Per ora, permettiamo solo ad un utente di vedere i propri dispositivi
        query["owner_id"] = current_user["id"]
    elif not owner_id:
        # Se non è specificato owner_id, mostra solo i dispositivi dell'utente corrente
        query["owner_id"] = current_user["id"]
    else:
        # Altrimenti, applica il filtro specificato
        query["owner_id"] = owner_id
        
    devices = await list_documents("devices", query)
    return devices

@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ottieni un dispositivo specifico tramite ID"""
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Verifica che l'utente corrente possa accedere a questo dispositivo
    if device.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per accedere a questo dispositivo"
        )
    
    return device

@router.put("/{device_id}", response_model=Device)
async def update_device(
    device_id: str, 
    device_update: Device = Body(...),
    regenerate_api_key: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Aggiorna un dispositivo esistente
    
    Supporta sia dispositivi basati su ontologia che su template
    """
    existing_device = await get_document("devices", device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Verifica che l'utente corrente possa modificare questo dispositivo
    if existing_device.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per modificare questo dispositivo"
        )
    
    # Verifica che device_update abbia o device_type o template_id
    if not device_update.device_type and not device_update.template_id:
        raise HTTPException(
            status_code=400,
            detail="È necessario specificare almeno uno tra device_type (ontologia) e template_id (template personalizzato)"
        )
    
    # Se viene fornito template_id, verifica che esista
    if device_update.template_id:
        template = await get_document("device_templates", device_update.template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template con ID '{device_update.template_id}' non trovato"
            )
    
    # Prepara i dati dell'aggiornamento
    update_data = device_update.dict(exclude_unset=True)
    
    # Gestione del cambio di proprietario
    old_owner_id = existing_device.get("owner_id")
    new_owner_id = device_update.owner_id
    
    # Verifica che l'utente corrente possa cambiare il proprietario
    if new_owner_id != old_owner_id and new_owner_id != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per trasferire questo dispositivo ad un altro utente"
        )
    
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
async def delete_device(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Elimina un dispositivo e il suo digital twin
    
    Aggiorna anche l'utente proprietario rimuovendo i riferimenti
    """
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Verifica che l'utente corrente possa eliminare questo dispositivo
    if device.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per eliminare questo dispositivo"
        )
    
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
async def regenerate_api_key(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Rigenera l'API key per un dispositivo
    
    Restituisce la nuova API key generata
    """
    device = await get_document("devices", device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    
    # Verifica che l'utente corrente possa modificare questo dispositivo
    if device.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per rigenerare l'API key di questo dispositivo"
        )
    
    # Genera una nuova API key
    new_api_key = secrets.token_urlsafe(32)
    
    # Aggiorna il dispositivo
    await update_document("devices", device_id, {"api_key": new_api_key})
    
    return {"api_key": new_api_key}

@router.post("/data", status_code=200)
async def send_device_data(
    data: Dict[str, Any] = Body(...),
    device: Device = Depends(get_device_by_api_key)
):
    """
    Invia dati da un dispositivo e aggiorna il suo digital twin
    
    Supporta sia dispositivi basati su ontologia che template
    """
    from app.models.sensor import SensorMeasurement
    import datetime
    from app.models.device_template import DeviceTemplate
    
    # Timestamp corrente
    now = datetime.datetime.utcnow().isoformat()
    
    # Validazione dei dati ricevuti
    valid_data = {}
    
    # Se il dispositivo è basato su template
    if device.get("template_id"):
        template = await get_document("device_templates", device["template_id"])
        if template:
            template_model = DeviceTemplate(**template)
            
            # Valida i dati rispetto al template
            for attr_name, value in data.items():
                if attr_name in template_model.attributes:
                    # Semplice validazione del tipo
                    if template_model.validate_attribute_value(attr_name, value):
                        valid_data[attr_name] = {
                            "value": value,
                            "unit_measure": template_model.attributes[attr_name].unit_measure or ""
                        }
    
    # Se il dispositivo è basato su ontologia
    elif device.get("device_type"):
        from app.ontology.manager import OntologyManager
        ontology = OntologyManager()
        
        for attr_name, value in data.items():
            # Verifica che l'attributo sia compatibile col tipo di dispositivo
            if ontology.is_sensor_compatible(device["device_type"], attr_name):
                valid_data[attr_name] = {
                    "value": value,
                    "unit_measure": ontology.get_sensor_details(attr_name).get("unit_measure", "")
                }
    
    # Aggiorna gli attributi nel dispositivo
    if valid_data:
        await update_document("devices", device["id"], {"attributes": valid_data})
        
        # Aggiorna anche il digital twin
        if device.get("digital_twin_id"):
            digital_twin = await get_document("digital_twins", device["digital_twin_id"])
            if digital_twin:
                twin_state = digital_twin.get("state", {})
                
                # Aggiorna lo stato con i nuovi valori
                for attr_name, attr_data in valid_data.items():
                    if attr_name not in twin_state:
                        twin_state[attr_name] = []
                    
                    # Aggiungi la nuova misurazione
                    twin_state[attr_name].append({
                        "timestamp": now,
                        "value": attr_data["value"],
                        "unit_measure": attr_data["unit_measure"]
                    })
                    
                    # Mantieni solo le ultime 100 misurazioni
                    if len(twin_state[attr_name]) > 100:
                        twin_state[attr_name] = twin_state[attr_name][-100:]
                
                await update_document("digital_twins", device["digital_twin_id"], {"state": twin_state})
        
        return {"status": "success", "updated_attributes": list(valid_data.keys())}
    else:
        return {"status": "warning", "message": "Nessun attributo valido fornito"}