# app/services/digital_twin_service.py
from app.models.digital_twin import DigitalTwin, DigitalReplicaLayer, SensorData
from app.models.device import Device
from app.db.crud import create_document, get_document, update_document
from app.ontology.manager import OntologyManager
from typing import Dict, List, Any, Optional
import datetime
import uuid

async def create_digital_twin_for_device(device: Dict[str, Any]) -> DigitalTwin:
    """Crea un digital twin per un dispositivo esistente"""
    # Inizializza le variabili per i sensori compatibili
    compatible_sensors = []
    available_ops = []
    dashboards = []
    
    # Gestione diversa in base al tipo di dispositivo (ontologia o template)
    if device.get('device_type'):
        # Inizializza il gestore dell'ontologia
        ontology = OntologyManager()
        
        # Crea il digital twin con i livelli appropriati
        digital_twin = DigitalTwin(
            name=f"DT_{device['name']}",
            device_id=device['id'],
            device_type=device.get('device_type'),
            owner_id=device.get('owner_id'),
            template_id=None
        )
        
        # Ottieni sensori compatibili
        compatible_sensors = ontology.get_compatible_sensors(device['device_type'])
        digital_twin.compatible_sensors = compatible_sensors
        
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
    
    elif device.get('template_id'):
        # Per i dispositivi basati su template
        template = await get_document("device_templates", device['template_id'])
        if not template:
            # Fallback a un digital twin generico se il template non esiste
            digital_twin = DigitalTwin(
                name=f"DT_{device['name']}",
                device_id=device['id'],
                device_type=None,
                owner_id=device.get('owner_id'),
                template_id=device.get('template_id')
            )
        else:
            # Crea il digital twin per device basato su template
            digital_twin = DigitalTwin(
                name=f"DT_{device['name']}",
                device_id=device['id'],
                device_type=None,
                owner_id=device.get('owner_id'),
                template_id=device.get('template_id')
            )
            
            # Per ogni attributo nel template, crea operazioni e dashboard generici
            for attr_name, attr_def in template.get("attributes", {}).items():
                compatible_sensors.append(attr_name)
                
                # Operazioni base per tutti gli attributi
                available_ops.append(f"track_{attr_name}")
                available_ops.append(f"view_{attr_name}_history")
                
                # Se l'attributo ha vincoli min/max, può supportare analisi sugli intervalli
                constraints = attr_def.get("constraints", {})
                if constraints and constraints.get("min_value") is not None and constraints.get("max_value") is not None:
                    available_ops.append(f"analyze_{attr_name}_range")
                    available_ops.append(f"compute_{attr_name}_statistics")
                
                # Se l'attributo ha unità di misura, può supportare conversioni
                if attr_def.get("unit_measure"):
                    available_ops.append(f"convert_{attr_name}_units")
                
                # Dashboard per ogni attributo
                dashboards.append(f"{attr_name}_dashboard")
            
            # Dashboard principale per il template
            dashboards.append(f"{template.get('name', 'template')}_main_dashboard")
            
            # Imposta i sensori compatibili
            digital_twin.compatible_sensors = compatible_sensors
    
    else:
        # Fallback per dispositivi senza tipo o template
        digital_twin = DigitalTwin(
            name=f"DT_{device['name']}",
            device_id=device['id'],
            owner_id=device.get('owner_id')
        )
    
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
    timestamp: Optional[str] = None,
    unit_measure: Optional[str] = ""
) -> bool:
    """Aggiunge dati del sensore al digital twin"""
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        return False
        
    if not timestamp:
        timestamp = datetime.datetime.now().isoformat()
        
    # Verifica se il sensore è compatibile con il digital twin
    if sensor_type not in dt.get("compatible_sensors", []):
        return False
    
    # Se non è stata specificata un'unità di misura e il digital twin è basato su ontologia
    if not unit_measure and dt.get("device_type"):
        # Ottieni l'unità di misura dall'ontologia
        ontology = OntologyManager()
        sensor_details = ontology.get_sensor_details(sensor_type)
        if sensor_details:
            unit_measures = sensor_details.get("unitMeasure")
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
    dt = await get_document("digital_twins", digital_twin_id)
    if not dt:
        return {"success": False, "message": "Digital Twin non trovato"}
    
    timestamp = datetime.datetime.now().isoformat()
    generated_data = {}
    
    # Se il digital twin è basato su ontologia
    if dt.get("device_type"):
        ontology = OntologyManager()
        
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
    
    # Se il digital twin è basato su template
    elif dt.get("template_id"):
        template = await get_document("device_templates", dt.get("template_id"))
        
        if template:
            import random
            
            for attr_name, attr_def in template.get("attributes", {}).items():
                # Genera un valore casuale in base al tipo e ai vincoli
                value = None
                attr_type = attr_def.get("type", "number")
                constraints = attr_def.get("constraints", {})
                
                # Genera valori in base al tipo
                if attr_type == "number":
                    min_val = constraints.get("min_value", 0)
                    max_val = constraints.get("max_value", 100)
                    value = round(random.uniform(min_val, max_val), 2)
                elif attr_type == "boolean":
                    value = random.choice([True, False])
                elif attr_type == "string" and constraints.get("enum_values"):
                    value = random.choice(constraints.get("enum_values"))
                    
                if value is not None:
                    # Aggiungi i dati al digital twin
                    unit_measure = attr_def.get("unit_measure", "")
                    success = await add_sensor_data_to_digital_twin(
                        digital_twin_id,
                        attr_name,
                        value,
                        timestamp,
                        unit_measure
                    )
                    if success:
                        generated_data[attr_name] = value
    
    return {
        "success": True,
        "timestamp": timestamp,
        "generated_data": generated_data
    }