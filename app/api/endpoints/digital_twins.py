# app/api/endpoints/digital_twins.py
from fastapi import APIRouter, HTTPException, Body, Query, Depends
from typing import List, Dict, Any, Optional
from app.models.digital_twin import DigitalTwin
from app.models.sensor import SensorMeasurement
from app.db.crud import get_document, update_document, delete_document, list_documents
from app.services.digital_twin_service import add_sensor_data_to_digital_twin, generate_random_sensor_data
from app.ontology.manager import OntologyManager
from app.api.auth import get_device_by_api_key, verify_device_ownership

router = APIRouter()

@router.get("/", response_model=List[DigitalTwin])
async def list_digital_twins(owner_id: Optional[str] = None):
    """Ottieni tutti i digital twins, opzionalmente filtrando per proprietario"""
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
        
    digital_twins = await list_documents("digital_twins", query)
    return digital_twins

@router.get("/{digital_twin_id}", response_model=DigitalTwin)
async def get_digital_twin(digital_twin_id: str):
    """Ottieni un digital twin specifico tramite ID"""
    digital_twin = await get_document("digital_twins", digital_twin_id)
    if not digital_twin:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
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

@router.post("/{digital_twin_id}/generate-data", status_code=201)
async def generate_data(digital_twin_id: str):
    """Genera dati casuali per tutti i sensori compatibili di un digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
        
    result = await generate_random_sensor_data(digital_twin_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.get("/{digital_twin_id}/data", response_model=Dict[str, List[Dict[str, Any]]])
async def get_sensor_data(
    digital_twin_id: str, 
    sensor_type: Optional[str] = None
):
    """Ottieni i dati dei sensori da un digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
        
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
async def check_sensor_compatibility(digital_twin_id: str, sensor_type: str):
    """Verifica se un tipo di sensore è compatibile con un digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Digital Twin non trovato")
        
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