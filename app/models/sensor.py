# app/models/sensor.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union

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

class SensorType(BaseModel):
    """Rappresenta un tipo di sensore dall'ontologia"""
    name: str
    superclass: List[str] = []
    unit_measure: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None

