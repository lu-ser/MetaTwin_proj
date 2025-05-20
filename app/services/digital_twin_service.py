# app/services/digital_twin_service.py
from app.models.digital_twin import DigitalTwin, DigitalReplicaLayer, SensorData
from app.models.device import Device
from app.db.crud import create_document, get_document, update_document
from app.ontology.manager import OntologyManager
from typing import Dict, List, Any, Optional
import datetime

async def create_digital_twin_for_device(device: Dict[str, Any]) -> DigitalTwin:
    """Crea un digital twin per un dispositivo esistente"""
    # Inizializza il gestore dell'ontologia
    ontology = OntologyManager()
    
    # Crea il digital twin con i livelli appropriati
    digital_twin = DigitalTwin(
        name=f"DT_{device['name']}",
        device_id=device['id'],
        device_type=device['device_type'],
        owner_id=device.get('owner_id')
    )
    
    # Ottieni sensori compatibili
    compatible_sensors = ontology.get_compatible_sensors(device['device_type'])
    digital_twin.compatible_sensors = compatible_sensors
    
    # Operazioni disponibili e dashboard vengono determinati esclusivamente 
    # dalle proprietà strutturali dei sensori nell'ontologia
    available_ops = []
    dashboards = []
    
    # Per ogni sensore compatibile, genera operazioni e dashboard in base alle sue proprietà
    for sensor_type in compatible_sensors:
        sensor_details = ontology.get_sensor_details(sensor_type)
        
        # Aggiungi operazioni basate sulla posizione del sensore nella gerarchia
        superclasses = ontology.get_all_superclasses(sensor_type)
        subclasses = ontology.get_all_subclasses(sensor_type)
        
        # Operazioni base per tutti i sensori
        available_ops.append(f"track_{sensor_type}")
        available_ops.append(f"view_{sensor_type}_history")
        
        # Se il sensore ha proprietà min/max, può supportare analisi sugli intervalli
        if all(k in sensor_details for k in ['min', 'max']):
            available_ops.append(f"analyze_{sensor_type}_range")
            
            # Se ha anche una media, può supportare rilevamento statistico
            if 'mean' in sensor_details:
                available_ops.append(f"compute_{sensor_type}_statistics")
        
        # Se il sensore ha unità di misura, può supportare conversioni
        if 'unitMeasure' in sensor_details and sensor_details['unitMeasure']:
            available_ops.append(f"convert_{sensor_type}_units")
        
        # Se è una classe radice (senza superclassi), può essere un sensore principale
        if not sensor_details.get('superclass'):
            dashboards.append(f"{sensor_type}_primary_dashboard")
            available_ops.append(f"manage_{sensor_type}_settings")
        
        # Se ha sottoclassi, può aggregare dati da diverse fonti
        if subclasses:
            available_ops.append(f"aggregate_{sensor_type}_data")
            dashboards.append(f"{sensor_type}_aggregated_view")
            
        # Se ha superclassi, può partecipare a dashboard di livello superiore
        if superclasses:
            for superclass in superclasses:
                dashboards.append(f"{superclass}_integrated_dashboard")
                
        # Dashboard specializzato per questo tipo di sensore
        dashboards.append(f"{sensor_type}_dashboard")
    
    # Rimuovi duplicati e assegna operazioni e dashboard
    digital_twin.service_layer.available_operations = list(set(available_ops))
    digital_twin.application_layer.dashboards = list(set(dashboards))
    
    # Crea configurazioni per i servizi
    digital_twin.service_layer.data_processing_configs = {
        "enabled": True,
        "sampling_rate": "auto",
        "storage_policy": "time_series",
        "aggregation_methods": ["avg", "min", "max"]
    }
    
    # Configura visualizzazioni
    digital_twin.application_layer.visualization_configs = {
        "default_view": "time_series",
        "available_views": ["time_series", "gauge", "numeric", "comparison"],
        "time_range_presets": ["last_hour", "last_day", "last_week", "last_month", "custom"]
    }
    
    # Salva il digital twin nel database
    dt_dict = digital_twin.dict()
    await create_document("digital_twins", dt_dict)
    
    # Aggiorna il dispositivo con l'ID del digital twin
    await update_document("devices", device['id'], {"digital_twin_id": digital_twin.id})
    
    return digital_twin

async def add_sensor_data_to_digital_twin(
    digital_twin_id: str, 
    sensor_type: str, 
    value: float,
    timestamp: Optional[str] = None
) -> bool:
    """Aggiunge dati del sensore al digital twin"""
    # Inizializza il gestore dell'ontologia
    ontology = OntologyManager()
    
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        return False
        
    if not timestamp:
        timestamp = datetime.datetime.now().isoformat()
        
    # Verifica se il sensore è compatibile con il digital twin
    if sensor_type not in dt.get("compatible_sensors", []):
        return False
        
    # Ottieni l'unità di misura dall'ontologia
    sensor_details = ontology.get_sensor_details(sensor_type)
    if not sensor_details:
        return False
        
    unit_measure = ""
    if "unitMeasure" in sensor_details:
        unit_measures = sensor_details["unitMeasure"]
        if isinstance(unit_measures, list) and len(unit_measures) > 0:
            unit_measure = unit_measures[0]
    
    # Prepara il dato del sensore
    sensor_data = SensorData(
        timestamp=timestamp,
        value=value,
        unit_measure=unit_measure
    )
    
    # Aggiorna il digital twin con il nuovo dato
    replica_path = f"digital_replica.sensor_data.{sensor_type}"
    
    # Verifica se esiste già una lista per questo tipo di sensore
    existing_dt = await get_document("digital_twins", digital_twin_id)
    if existing_dt and "digital_replica" in existing_dt and "sensor_data" in existing_dt["digital_replica"]:
        sensor_data_dict = existing_dt["digital_replica"]["sensor_data"]
        if sensor_type in sensor_data_dict:
            # Aggiungi alla lista esistente
            update_result = await update_document(
                "digital_twins", 
                digital_twin_id,
                {f"{replica_path}": sensor_data_dict[sensor_type] + [sensor_data.dict()]}
            )
        else:
            # Crea una nuova lista
            update_result = await update_document(
                "digital_twins", 
                digital_twin_id,
                {f"{replica_path}": [sensor_data.dict()]}
            )
    else:
        # Inizializza il dizionario dei dati del sensore
        update_result = await update_document(
            "digital_twins", 
            digital_twin_id,
            {f"{replica_path}": [sensor_data.dict()]}
        )
    
    # Aggiorna anche last_updated
    await update_document(
        "digital_twins",
        digital_twin_id,
        {"digital_replica.last_updated": timestamp}
    )
    
    return True

async def generate_random_sensor_data(digital_twin_id: str) -> Dict[str, Any]:
    """Genera dati random per tutti i sensori compatibili di un digital twin"""
    ontology = OntologyManager()
    
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        return {"success": False, "message": "Digital Twin non trovato"}
    
    timestamp = datetime.datetime.now().isoformat()
    generated_data = {}
    
    for sensor_type in dt.get("compatible_sensors", []):
        # Genera un valore casuale per questo tipo di sensore
        value = ontology.generate_random_value_for_sensor(sensor_type)
        
        if value is not None:
            # Aggiungi i dati al digital twin
            success = await add_sensor_data_to_digital_twin(
                digital_twin_id,
                sensor_type,
                value,
                timestamp
            )
            
            if success:
                generated_data[sensor_type] = value
    
    return {
        "success": True, 
        "timestamp": timestamp, 
        "data": generated_data
    }