# app/models/digital_twin.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import uuid
from ..ontology.manager import OntologyManager

class SensorData(BaseModel):
    """Rappresenta i dati di un singolo sensore"""
    timestamp: str
    value: float
    unit_measure: str = ""

class DigitalReplicaLayer(BaseModel):
    """Livello che memorizza i dati del dispositivo fisico"""
    sensor_data: Dict[str, List[SensorData]] = Field(default_factory=dict)
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceLayer(BaseModel):
    """Livello che fornisce servizi e operazioni sui dati"""
    available_operations: List[str] = []
    data_processing_configs: Dict[str, Any] = Field(default_factory=dict)
    analytics_configs: Dict[str, Any] = Field(default_factory=dict)

class ApplicationLayer(BaseModel):
    """Livello che contiene applicazioni e visualizzazioni"""
    dashboards: List[str] = []
    visualization_configs: Dict[str, Any] = Field(default_factory=dict)
    user_interfaces: List[str] = []

class DigitalTwin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    device_id: str
    device_type: str
    digital_replica: DigitalReplicaLayer = Field(default_factory=DigitalReplicaLayer)
    service_layer: ServiceLayer = Field(default_factory=ServiceLayer)
    application_layer: ApplicationLayer = Field(default_factory=ApplicationLayer)
    compatible_sensors: List[str] = []
    owner_id: Optional[str] = None
    
    @validator('device_type')
    def validate_device_type(cls, v):
        """Valida che il tipo di dispositivo sia definito nell'ontologia"""
        ontology = OntologyManager()
        if v not in ontology.get_all_sensor_types():
            raise ValueError(f"Il tipo di dispositivo '{v}' non è definito nell'ontologia")
        return v
    
    @validator('compatible_sensors', always=True)
    def set_compatible_sensors(cls, v, values):
        """Imposta automaticamente i sensori compatibili in base al tipo di dispositivo"""
        if 'device_type' not in values:
            return v
            
        device_type = values['device_type']
        ontology = OntologyManager()
        return ontology.get_compatible_sensors(device_type)