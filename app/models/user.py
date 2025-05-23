# app/models/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = None
    devices: List[str] = []  # Lista di device IDs
    digital_twins: List[str] = []  # Lista di digital twin IDs