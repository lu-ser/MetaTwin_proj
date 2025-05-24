from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
import uuid
from enum import Enum


class AttributeType(str, Enum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class AttributeConstraint(BaseModel):
    """Constraints for attribute values"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for string validation
    enum_values: Optional[List[Any]] = None  # Possible values
    required: bool = False


class AttributeDefinition(BaseModel):
    """Definition of a sensor attribute within a template"""
    name: str
    type: AttributeType
    unit_measure: Optional[str] = None
    description: Optional[str] = ""
    constraints: Optional[AttributeConstraint] = None
    default_value: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceTemplate(BaseModel):
    """Template defining the structure of a device and its sensors"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    attributes: Dict[str, AttributeDefinition]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
    owner_id: Optional[str] = None
    is_ontology_based: bool = False  # False for custom templates, True for ontology-based
    
    def validate_attribute_value(self, attribute_name: str, value: Any) -> bool:
        """Validates a value against attribute definition constraints"""
        if attribute_name not in self.attributes:
            return False
            
        attr_def = self.attributes[attribute_name]
        attr_type = attr_def.type
        
        # Type validation
        if attr_type == AttributeType.NUMBER and not isinstance(value, (int, float)):
            return False
        elif attr_type == AttributeType.STRING and not isinstance(value, str):
            return False
        elif attr_type == AttributeType.BOOLEAN and not isinstance(value, bool):
            return False
        elif attr_type == AttributeType.OBJECT and not isinstance(value, dict):
            return False
        elif attr_type == AttributeType.ARRAY and not isinstance(value, list):
            return False
            
        # Constraint validation if present
        if attr_def.constraints:
            constraints = attr_def.constraints
            
            if attr_type == AttributeType.NUMBER:
                if constraints.min_value is not None and value < constraints.min_value:
                    return False
                if constraints.max_value is not None and value > constraints.max_value:
                    return False
            elif attr_type == AttributeType.STRING and constraints.pattern:
                import re
                if not re.match(constraints.pattern, value):
                    return False
            
            if constraints.enum_values and value not in constraints.enum_values:
                return False
                
        return True
    
    def generate_default_values(self) -> Dict[str, Any]:
        """Generates default values for all attributes in the template"""
        result = {}
        for name, attr_def in self.attributes.items():
            if attr_def.default_value is not None:
                result[name] = attr_def.default_value
        return result 