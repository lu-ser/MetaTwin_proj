# app/models/digital_twin.py
from pydantic import BaseModel, Field, validator, model_validator
from typing import Dict, List, Optional, Any
import uuid
from ..ontology.manager import OntologyManager

class SensorData(BaseModel):
    """Represents data from a single sensor"""
    timestamp: str
    value: Any
    unit_measure: str = ""

class DigitalReplicaLayer(BaseModel):
    """Layer that stores physical device data"""
    sensor_data: Dict[str, List[SensorData]] = Field(default_factory=dict)
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceLayer(BaseModel):
    """Layer that provides services and operations on data"""
    available_operations: List[str] = []
    data_processing_configs: Dict[str, Any] = Field(default_factory=dict)
    analytics_configs: Dict[str, Any] = Field(default_factory=dict)

class ApplicationLayer(BaseModel):
    """Layer that contains applications and visualizations"""
    dashboards: List[str] = []
    visualization_configs: Dict[str, Any] = Field(default_factory=dict)
    user_interfaces: List[str] = []

class DigitalTwin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    device_id: str
    device_type: Optional[str] = None
    template_id: Optional[str] = None
    digital_replica: DigitalReplicaLayer = Field(default_factory=DigitalReplicaLayer)
    service_layer: ServiceLayer = Field(default_factory=ServiceLayer)
    application_layer: ApplicationLayer = Field(default_factory=ApplicationLayer)
    compatible_sensors: List[str] = []
    owner_id: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_configuration(self):
        """Validates the general configuration of the digital twin"""
        # For digital twins linked to the ontology, device_type is required
        # For digital twins based on templates, template_id is required
        # Generic digital twins can have neither
        
        return self
    
    @validator('device_type')
    def validate_device_type(cls, v):
        """Validates that the device type is defined in the ontology if specified"""
        if v is not None:
            ontology = OntologyManager()
            if v not in ontology.get_all_sensor_types():
                raise ValueError(f"Device type '{v}' is not defined in the ontology")
        return v
    
    @validator('compatible_sensors', always=True)
    def set_compatible_sensors(cls, v, values):
        """Automatically sets compatible sensors based on device type or keeps unchanged"""
        # If compatible sensors have already been specified, respect the choice
        if v:
            return v
            
        # If device_type is present, use the ontology
        if 'device_type' in values and values['device_type']:
            device_type = values['device_type']
            ontology = OntologyManager()
            return ontology.get_compatible_sensors(device_type)
        
        # Otherwise (template_id or generic), use an empty list
        return []