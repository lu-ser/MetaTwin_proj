from pydantic import BaseModel, Field, validator, model_validator
from typing import Dict, List, Optional, Any, Union
import uuid
import secrets
from app.ontology.manager import OntologyManager

class SensorAttribute(BaseModel):
    """Represents a sensor attribute with value and unit of measurement"""
    value: Any
    unit_measure: Optional[str] = ""


class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    device_type: Optional[str] = None
    template_id: Optional[str] = None
    attributes: Dict[str, SensorAttribute] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    digital_twin_id: Optional[str] = None
    owner_id: Optional[str] = None
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    @model_validator(mode='after')
    def validate_device_config(self):
        """Validates that the device has device_type (ontology) or template_id (template)"""
        if not self.device_type and not self.template_id:
            raise ValueError("Either device_type or template_id must be specified")
            
        return self
    
    @validator('device_type')
    def validate_device_type(cls, v, values):
        """Validates that the device type is defined in the ontology if specified"""
        if v is not None:
            ontology = OntologyManager()
            if v not in ontology.get_all_sensor_types():
                raise ValueError(f"Device type '{v}' is not defined in the ontology")
        return v
    
class Config:
    # Permetti la creazione di attributi anche se la validazione fallisce
    validate_assignment = True