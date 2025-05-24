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
    
    @validator('attributes')
    def validate_attributes(cls, v, values):
        """Validates attributes based on validation type (ontology or template)"""
        from app.db.crud import get_document
        import asyncio
        
        device_type = values.get('device_type')
        template_id = values.get('template_id')
        
        # If device_type is present, use the ontology
        if device_type:
            ontology = OntologyManager()
            for attr_name in v.keys():
                if not ontology.is_sensor_compatible(device_type, attr_name):
                    raise ValueError(f"Attribute '{attr_name}' is not compatible with device type '{device_type}'")
        
        # If template_id is present, validate based on template
        elif template_id:
            # Note: here we use run_sync to synchronously execute an asynchronous function
            # in a synchronous validation environment. In a real scenario, you might need to
            # implement this validation more efficiently
            template = asyncio.get_event_loop().run_until_complete(
                get_document("device_templates", template_id)
            )
            
            if not template:
                raise ValueError(f"Template with ID '{template_id}' not found")
            
            from app.models.device_template import DeviceTemplate
            template_model = DeviceTemplate(**template)
            
            # Verify required attributes
            required_attrs = [
                name for name, attr_def in template_model.attributes.items() 
                if attr_def.constraints and attr_def.constraints.required
            ]
            for req_attr in required_attrs:
                if req_attr not in v:
                    raise ValueError(f"Required attribute '{req_attr}' is missing")
            
            # Validate the value of each attribute
            for attr_name, attr in v.items():
                if attr_name not in template_model.attributes:
                    raise ValueError(f"Attribute '{attr_name}' is not defined in the template")
                
                if not template_model.validate_attribute_value(attr_name, attr.value):
                    raise ValueError(f"Value of attribute '{attr_name}' is not valid")
                
                # Verify unit of measurement
                expected_unit = template_model.attributes[attr_name].unit_measure
                if expected_unit and attr.unit_measure != expected_unit:
                    raise ValueError(f"Invalid unit of measure for '{attr_name}', expected: {expected_unit}")
        
        return v