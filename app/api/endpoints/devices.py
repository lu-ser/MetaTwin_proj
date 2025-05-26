# app/api/endpoints/devices.py
from fastapi import APIRouter, HTTPException, Body, Depends, Header, Query, Path
from typing import List, Optional, Dict, Any, Union
from app.models.device import Device, SensorAttribute
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.services.digital_twin_service import create_digital_twin_for_device
from app.api.auth import get_device_by_api_key, verify_device_ownership
from app.api.auth_service import get_current_active_user
import secrets
router = APIRouter()
@router.post("/debug", status_code=200)
async def debug_create_device(
    data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Endpoint di debug per testare POST"""
    return {
        "status": "success",
        "received_data": data,
        "user": current_user["id"]
    }
@router.post("/", response_model=Device, status_code=201)
async def create_device(
    device_data: Dict[str, Any] = Body(...),  # Cambiato da Device a Dict
    regenerate_api_key: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Crea un nuovo dispositivo e il suo digital twin
    
    Il dispositivo può essere basato sull'ontologia (device_type) o su un template (template_id)
    """
    # Se l'owner_id non è specificato, imposta l'utente corrente come proprietario
    if "owner_id" not in device_data or not device_data["owner_id"]:
        device_data["owner_id"] = current_user["id"]
    
    # Verifica che l'utente corrente possa creare un dispositivo per il proprietario specificato
    if device_data["owner_id"] != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per creare dispositivi per altri utenti"
        )
    
    # Verifica che il device abbia o device_type o template_id
    device_type = device_data.get("device_type")
    template_id = device_data.get("template_id")
    
    if not device_type and not template_id:
        raise HTTPException(
            status_code=400,
            detail="È necessario specificare almeno uno tra device_type (ontologia) e template_id (template personalizzato)"
        )
    
    # Validazione dell'ontologia se device_type è presente
    if device_type:
        try:
            ontology = OntologyManager()
            if device_type not in ontology.get_all_sensor_types():
                raise HTTPException(
                    status_code=400,
                    detail=f"Device type '{device_type}' non trovato nell'ontologia"
                )
        except Exception as e:
            print(f"Warning: Ontology validation failed: {e}")
    
    # Validazione del template se template_id è presente
    if template_id:
        template = await get_document("device_templates", template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template con ID '{template_id}' non trovato"
            )
    
    # Converti gli attributi nel formato corretto
    processed_attributes = {}
    if "attributes" in device_data and device_data["attributes"]:
        for attr_name, attr_data in device_data["attributes"].items():
            if isinstance(attr_data, dict):
                processed_attributes[attr_name] = SensorAttribute(
                    value=attr_data.get("value", 0),
                    unit_measure=attr_data.get("unit_measure", "")
                )
            else:
                # Fallback per dati in formato diverso
                processed_attributes[attr_name] = SensorAttribute(
                    value=attr_data,
                    unit_measure=""
                )
    
    # Crea l'oggetto Device
    try:
        device = Device(
            name=device_data["name"],
            device_type=device_type,
            template_id=template_id,
            attributes=processed_attributes,
            owner_id=device_data["owner_id"],
            metadata=device_data.get("metadata", {})
        )
        
        # Se è richiesto di rigenerare API key o non è presente
        if regenerate_api_key or not device.api_key:
            device.api_key = secrets.token_urlsafe(32)
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Errore nella creazione del dispositivo: {str(e)}"
        )
    
    # Salva il dispositivo nel database
    device_dict = device.dict()
    device_id = await create_document("devices", device_dict)
    
    # Ottieni il documento completo del dispositivo salvato
    saved_device = await get_document("devices", device.id)
    
    # Crea un digital twin per questo dispositivo
    try:
        digital_twin = await create_digital_twin_for_device(saved_device)
        
        # Aggiorna il dispositivo con l'ID del digital twin
        await update_document("devices", device.id, {"digital_twin_id": digital_twin.id})
    except Exception as e:
        print(f"Warning: Could not create digital twin: {e}")
        # Non bloccare la creazione del dispositivo se il digital twin fallisce
    
    # Se è specificato un proprietario, aggiorna anche l'utente
    if device.owner_id:
        try:
            user = await get_document("users", device.owner_id)
            if user:
                # Aggiungi l'ID del dispositivo alla lista dei dispositivi dell'utente
                user_devices = user.get("devices", [])
                if device.id not in user_devices:
                    user_devices.append(device.id)
                    
                user_digital_twins = user.get("digital_twins", [])
                if hasattr(digital_twin, 'id') and digital_twin.id not in user_digital_twins:
                    user_digital_twins.append(digital_twin.id)
                    
                await update_document("users", device.owner_id, {
                    "devices": user_devices,
                    "digital_twins": user_digital_twins
                })
        except Exception as e:
            print(f"Warning: Could not update user: {e}")
    
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
    from app.services.digital_twin_service import add_sensor_data_to_digital_twin
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
                unit_measure = ""
                sensor_details = ontology.get_sensor_details(attr_name)
                if sensor_details and "unitMeasure" in sensor_details:
                    unit_measures = sensor_details["unitMeasure"]
                    if isinstance(unit_measures, list) and len(unit_measures) > 0:
                        unit_measure = unit_measures[0]
                
                valid_data[attr_name] = {
                    "value": value,
                    "unit_measure": unit_measure
                }
    
    # Aggiorna gli attributi nel dispositivo
    if valid_data:
        await update_document("devices", device["id"], {"attributes": valid_data})
        
        #CORREZIONE: Usa il servizio dedicato per aggiornare il digital twin
        if device.get("digital_twin_id"):
            updated_sensors = []
            
            for attr_name, attr_data in valid_data.items():
                success = await add_sensor_data_to_digital_twin(
                    device["digital_twin_id"],
                    attr_name,
                    attr_data["value"],
                    now,
                    attr_data["unit_measure"]
                )
                
                if success:
                    updated_sensors.append(attr_name)
            
            return {
                "status": "success", 
                "updated_attributes": list(valid_data.keys()),
                "digital_twin_updated": len(updated_sensors) > 0,
                "updated_sensors": updated_sensors
            }
        
        return {"status": "success", "updated_attributes": list(valid_data.keys())}
    else:
        return {"status": "warning", "message": "Nessun attributo valido fornito"}

