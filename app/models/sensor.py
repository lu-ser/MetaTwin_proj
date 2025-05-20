# app/models/sensor.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
import json
import os
from app.config import settings


with open(settings.CLASS_HIERARCHY_PATH, "r") as f:
    CLASS_HIERARCHY = json.load(f)

class SensorAttribute(BaseModel):
    """Rappresenta un attributo di un sensore con valore e unità di misura"""
    value: float
    unit_measure: str

class SensorMeasurement(BaseModel):
    """Rappresenta una misurazione di un sensore"""
    timestamp: str
    attribute_name: str
    value: float
    unit_measure: str = ""

    @validator('attribute_name')
    def validate_attribute(cls, v):
        if v not in CLASS_HIERARCHY:
            raise ValueError(f"Attributo sconosciuto: {v}")
        return v

class SensorType(BaseModel):
    """Rappresenta un tipo di sensore dall'ontologia"""
    name: str
    superclass: List[str] = []
    unit_measure: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None

    @validator('name')
    def validate_sensor_type(cls, v):
        if v not in CLASS_HIERARCHY:
            raise ValueError(f"Tipo di sensore sconosciuto: {v}")
        return v