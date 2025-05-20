# app/models/device.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import uuid
from app.ontology.manager import OntologyManager

class SensorAttribute(BaseModel):
    """Rappresenta un attributo di un sensore con valore e unità di misura"""
    value: float
    unit_measure: str = ""

class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    device_type: str
    attributes: Dict[str, SensorAttribute] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    digital_twin_id: Optional[str] = None
    owner_id: Optional[str] = None
    
    @validator('device_type')
    def validate_device_type(cls, v):
        """Valida che il tipo di dispositivo sia definito nell'ontologia"""
        ontology = OntologyManager()
        if v not in ontology.get_all_sensor_types():
            raise ValueError(f"Il tipo di dispositivo '{v}' non è definito nell'ontologia")
        return v
    
    @validator('attributes')
    def validate_attributes(cls, v, values):
        """Valida che gli attributi siano compatibili con il tipo di dispositivo"""
        if 'device_type' not in values:
            return v
            
        device_type = values['device_type']
        ontology = OntologyManager()
        
        for attr_name in v.keys():
            if not ontology.is_sensor_compatible(device_type, attr_name):
                raise ValueError(f"L'attributo '{attr_name}' non è compatibile con il tipo di dispositivo '{device_type}'")
                
        return v