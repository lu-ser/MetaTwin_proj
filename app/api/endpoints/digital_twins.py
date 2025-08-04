# app/api/endpoints/digital_twins.py
from fastapi import APIRouter, HTTPException, Body, Query, Depends
from typing import List, Dict, Any, Optional
from app.models.digital_twin import DigitalTwin
from app.models.sensor import SensorMeasurement, BatchSensorMeasurements
from app.db.crud import get_document, update_document, delete_document, list_documents
from app.services.digital_twin_service import add_sensor_data_to_digital_twin, generate_random_sensor_data
from app.ontology.manager import OntologyManager
from app.api.auth import get_device_by_api_key, verify_device_ownership
from app.api.auth_service import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[DigitalTwin])
async def list_digital_twins(
    owner_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ottieni tutti i digital twins, opzionalmente filtrando per proprietario"""
    query = {}
    
    # Se viene specificato un owner_id, verifica che l'utente possa vedere questi digital twins
    if owner_id and owner_id != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        # Per ora, permettiamo solo ad un utente di vedere i propri digital twins
        query["owner_id"] = current_user["id"]
    elif not owner_id:
        # Se non è specificato owner_id, mostra solo i digital twins dell'utente corrente
        query["owner_id"] = current_user["id"]
    else:
        # Altrimenti, applica il filtro specificato
        query["owner_id"] = owner_id
        
    digital_twins = await list_documents("digital_twins", query)
    return digital_twins

@router.get("/{digital_twin_id}", response_model=DigitalTwin)
async def get_digital_twin(
    digital_twin_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ottieni un digital twin specifico tramite ID"""
    digital_twin = await get_document("digital_twins", digital_twin_id)
    if not digital_twin:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
    
    # Verifica che l'utente corrente possa accedere a questo digital twin
    if digital_twin.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per accedere a questo Digital Twin"
        )
    
    return digital_twin

@router.post("/{digital_twin_id}/data", status_code=201)
async def add_sensor_measurement(
    digital_twin_id: str, 
    measurement: SensorMeasurement,
    authenticated_device = Depends(get_device_by_api_key)
):
    """
    Aggiungi una nuova misurazione al digital twin
    
    Richiede autenticazione tramite API key del dispositivo
    """
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
    
    # Verifica che il digital twin appartenga al dispositivo autenticato
    if dt.get("device_id") != authenticated_device.get("id"):
        raise HTTPException(
            status_code=403,
            detail="Non sei autorizzato a inviare dati a questo Digital Twin"
        )
    
    # Verifica che il sensore sia compatibile con il digital twin
    if measurement.attribute_name not in dt.get("compatible_sensors", []):
        raise HTTPException(
            status_code=400, 
            detail=f"Il sensore '{measurement.attribute_name}' non è compatibile con questo Digital Twin"
        )
        
    success = await add_sensor_data_to_digital_twin(
        digital_twin_id,
        measurement.attribute_name,
        measurement.value,
        measurement.timestamp
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Impossibile aggiungere i dati del sensore")
        
    return {"message": "Dati del sensore aggiunti con successo"}

@router.post("/{digital_twin_id}/data/batch", status_code=201)
async def add_batch_sensor_measurements(
    digital_twin_id: str, 
    batch: BatchSensorMeasurements,
    authenticated_device = Depends(get_device_by_api_key)
):
    """
    Aggiungi multiple misurazioni al digital twin in una singola richiesta
    
    Richiede autenticazione tramite API key del dispositivo
    """
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
    
    # Verifica che il digital twin appartenga al dispositivo autenticato
    if dt.get("device_id") != authenticated_device.get("id"):
        raise HTTPException(
            status_code=403,
            detail="Non sei autorizzato a inviare dati a questo Digital Twin"
        )
    
    # Verifica che tutti i sensori siano compatibili con il digital twin
    compatible_sensors = dt.get("compatible_sensors", [])
    failed_measurements = []
    successful_count = 0
    
    for i, measurement in enumerate(batch.measurements):
        if measurement.attribute_name not in compatible_sensors:
            failed_measurements.append({
                "index": i,
                "attribute_name": measurement.attribute_name,
                "error": f"Il sensore '{measurement.attribute_name}' non è compatibile con questo Digital Twin"
            })
            continue
            
        success = await add_sensor_data_to_digital_twin(
            digital_twin_id,
            measurement.attribute_name,
            measurement.value,
            measurement.timestamp
        )
        
        if success:
            successful_count += 1
        else:
            failed_measurements.append({
                "index": i,
                "attribute_name": measurement.attribute_name,
                "error": "Impossibile aggiungere i dati del sensore"
            })
    
    result = {
        "message": f"Processate {len(batch.measurements)} misurazioni",
        "successful": successful_count,
        "failed": len(failed_measurements)
    }
    
    if failed_measurements:
        result["errors"] = failed_measurements
    
    return result

@router.post("/{digital_twin_id}/generate-data", status_code=201)
async def generate_data(
    digital_twin_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Genera dati casuali per tutti i sensori compatibili di un digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
    
    # Verifica che l'utente corrente possa accedere a questo digital twin
    if dt.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per accedere a questo Digital Twin"
        )
        
    result = await generate_random_sensor_data(digital_twin_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.get("/{digital_twin_id}/data", response_model=Dict[str, List[Dict[str, Any]]])
async def get_sensor_data(
    digital_twin_id: str, 
    sensor_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ottieni i dati dei sensori da un digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
    
    # Verifica che l'utente corrente possa accedere a questo digital twin
    if dt.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per accedere a questo Digital Twin"
        )
        
    if not dt.get("digital_replica") or not dt["digital_replica"].get("sensor_data"):
        return {}
        
    sensor_data = dt["digital_replica"]["sensor_data"]
    
    if sensor_type:
        # Restituisci solo i dati per un tipo specifico di sensore
        if sensor_type in sensor_data:
            return {sensor_type: sensor_data[sensor_type]}
        return {}
        
    return sensor_data

@router.get("/{digital_twin_id}/compatibility", response_model=Dict[str, Any])
async def check_sensor_compatibility(
    digital_twin_id: str, 
    sensor_type: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Verifica se un tipo di sensore è compatibile con un digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
    
    # Verifica che l'utente corrente possa accedere a questo digital twin
    if dt.get("owner_id") != current_user["id"]:
        # Qui potresti implementare controlli di ruolo più avanzati (es. admin)
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per accedere a questo Digital Twin"
        )
        
    ontology = OntologyManager()
    
    is_compatible = sensor_type in dt.get("compatible_sensors", [])
    
    # Ottieni ulteriori informazioni sul sensore dall'ontologia
    sensor_details = ontology.get_sensor_details(sensor_type) or {}
    
    # Ottieni le superclassi e sottoclassi
    superclasses = ontology.get_all_superclasses(sensor_type)
    subclasses = ontology.get_all_subclasses(sensor_type)
    
    return {
        "is_compatible": is_compatible,
        "sensor_type": sensor_type,
        "digital_twin_type": dt["device_type"],
        "sensor_details": sensor_details,
        "superclasses": superclasses,
        "subclasses": subclasses
    }

@router.get("/ontology/classes", response_model=List[str])
async def get_ontology_classes():
    """Ottieni tutte le classi definite nell'ontologia"""
    ontology = OntologyManager()
    return ontology.get_all_sensor_types()

@router.get("/ontology/root-classes", response_model=List[str])
async def get_ontology_root_classes():
    """Ottieni le classi radice dell'ontologia"""
    ontology = OntologyManager()
    return ontology.get_root_classes()

@router.get("/ontology/class/{class_name}", response_model=Dict[str, Any])
async def get_ontology_class_details(class_name: str):
    """Ottieni dettagli di una classe specifica dell'ontologia"""
    ontology = OntologyManager()
    
    details = ontology.get_sensor_details(class_name)
    if not details:
        raise HTTPException(status_code=404, detail=f"Classe '{class_name}' non trovata nell'ontologia")
        
    # Aggiungi superclassi e sottoclassi alle informazioni
    superclasses = ontology.get_all_superclasses(class_name)
    subclasses = ontology.get_all_subclasses(class_name)
    
    return {
        "name": class_name,
        "details": details,
        "superclasses": superclasses,
        "subclasses": subclasses
    }

@router.post("/", response_model=DigitalTwin, status_code=201)
async def create_digital_twin(
    digital_twin_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Crea un nuovo digital twin direttamente"""
    
    # Se l'owner_id non è specificato, imposta l'utente corrente come proprietario
    if "owner_id" not in digital_twin_data:
        digital_twin_data["owner_id"] = current_user["id"]
    
    # Verifica che l'utente corrente possa creare un digital twin per il proprietario specificato
    if digital_twin_data["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403, 
            detail="Non hai i permessi per creare digital twin per altri utenti"
        )
    
    # Se viene specificato un device_type, verifica che esista nell'ontologia
    if "device_type" in digital_twin_data and digital_twin_data["device_type"]:
        ontology = OntologyManager()
        if digital_twin_data["device_type"] not in ontology.get_all_sensor_types():
            raise HTTPException(
                status_code=400,
                detail=f"Device type '{digital_twin_data['device_type']}' non trovato nell'ontologia"
            )
    
    # Se viene specificato un template_id, verifica che esista
    if "template_id" in digital_twin_data and digital_twin_data["template_id"]:
        template = await get_document("device_templates", digital_twin_data["template_id"])
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template con ID '{digital_twin_data['template_id']}' non trovato"
            )
    
    # Crea prima un dispositivo se non esiste
    device_data = {
        "name": digital_twin_data.get("name", "Device") + "_Device",
        "owner_id": digital_twin_data["owner_id"],
        "attributes": {}
    }
    
    # Imposta device_type o template_id nel dispositivo
    if "device_type" in digital_twin_data:
        device_data["device_type"] = digital_twin_data["device_type"]
    if "template_id" in digital_twin_data:
        device_data["template_id"] = digital_twin_data["template_id"]
    
    # Crea il dispositivo
    device_id = await create_document("devices", device_data)
    device = await get_document("devices", device_id)
    
    # Crea il digital twin tramite il servizio
    digital_twin = await create_digital_twin_for_device(device)
    
    # Aggiorna il nome se specificato
    if "name" in digital_twin_data and digital_twin_data["name"] != digital_twin.name:
        await update_document("digital_twins", digital_twin.id, {
            "name": digital_twin_data["name"]
        })
        digital_twin.name = digital_twin_data["name"]
    
    # Aggiorna l'utente con il nuovo digital twin
    if digital_twin_data["owner_id"]:
        user = await get_document("users", digital_twin_data["owner_id"])
        if user:
            # Aggiungi il dispositivo
            user_devices = user.get("devices", [])
            if device_id not in user_devices:
                user_devices.append(device_id)
            
            # Aggiungi il digital twin
            user_digital_twins = user.get("digital_twins", [])
            if digital_twin.id not in user_digital_twins:
                user_digital_twins.append(digital_twin.id)
            
            await update_document("users", digital_twin_data["owner_id"], {
                "devices": user_devices,
                "digital_twins": user_digital_twins
            })
    
    return digital_twin