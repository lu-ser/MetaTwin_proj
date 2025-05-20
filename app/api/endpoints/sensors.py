# app/api/endpoints/sensors.py
from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Dict, Any, Optional
from app.models.sensor import SensorMeasurement, SensorType
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.ontology.manager import OntologyManager

router = APIRouter()

@router.get("/types", response_model=List[str])
async def get_sensor_types():
    """Ottiene tutti i tipi di sensori definiti nell'ontologia"""
    ontology = OntologyManager()
    return ontology.get_all_sensor_types()

@router.get("/types/{sensor_type}", response_model=Dict[str, Any])
async def get_sensor_type_details(sensor_type: str):
    """Ottiene i dettagli di un tipo di sensore specifico"""
    ontology = OntologyManager()
    details = ontology.get_sensor_details(sensor_type)
    
    if not details:
        raise HTTPException(status_code=404, detail=f"Tipo di sensore '{sensor_type}' non trovato")
    
    # Aggiungi informazioni strutturali
    superclasses = ontology.get_all_superclasses(sensor_type)
    subclasses = ontology.get_all_subclasses(sensor_type)
    
    result = {
        "name": sensor_type,
        "details": details,
        "superclasses": superclasses,
        "subclasses": subclasses
    }
    
    return result

@router.get("/hierarchy", response_model=Dict[str, List[str]])
async def get_sensor_hierarchy():
    """Ottiene la gerarchia completa dei sensori"""
    ontology = OntologyManager()
    result = {}
    
    # Ottieni tutte le classi radice
    root_classes = ontology.get_root_classes()
    result["root_classes"] = root_classes
    
    # Per ogni classe radice, costruisci l'albero delle sottoclassi
    class_trees = {}
    for root in root_classes:
        subclasses = ontology.get_all_subclasses(root)
        class_trees[root] = subclasses
    
    result["class_trees"] = class_trees
    
    return result

@router.get("/compatibility", response_model=Dict[str, List[str]])
async def check_sensors_compatibility(device_type: str):
    """Verifica quali sensori sono compatibili con un tipo di dispositivo"""
    ontology = OntologyManager()
    
    if device_type not in ontology.get_all_sensor_types():
        raise HTTPException(status_code=404, detail=f"Tipo di dispositivo '{device_type}' non trovato")
    
    compatible_sensors = ontology.get_compatible_sensors(device_type)
    
    return {
        "device_type": device_type,
        "compatible_sensors": compatible_sensors
    }

@router.post("/measurements", status_code=201)
async def add_sensor_measurement(measurement: SensorMeasurement):
    """Salva una misurazione di un sensore come documento separato"""
    # Salva la misurazione nel database
    measurement_dict = measurement.dict()
    
    # Ottieni l'unità di misura dall'ontologia se non specificata
    if not measurement.unit_measure:
        ontology = OntologyManager()
        sensor_details = ontology.get_sensor_details(measurement.attribute_name)
        if sensor_details and "unitMeasure" in sensor_details:
            unit_measures = sensor_details["unitMeasure"]
            if isinstance(unit_measures, list) and len(unit_measures) > 0:
                measurement_dict["unit_measure"] = unit_measures[0]
    
    # Aggiungi al database
    await create_document("sensor_measurements", measurement_dict)
    
    return {"message": "Misurazione salvata con successo"}

@router.get("/measurements", response_model=List[Dict[str, Any]])
async def get_sensor_measurements(
    sensor_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100
):
    """Ottiene le misurazioni dei sensori con filtri opzionali"""
    query = {}
    
    if sensor_type:
        query["attribute_name"] = sensor_type
    
    if start_time or end_time:
        query["timestamp"] = {}
        if start_time:
            query["timestamp"]["$gte"] = start_time
        if end_time:
            query["timestamp"]["$lte"] = end_time
    
    # Utilizza la funzione list_documents con il limite specificato
    db = get_database()
    collection = db["sensor_measurements"]
    cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    measurements = await cursor.to_list(length=limit)
    
    return measurements