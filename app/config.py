from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import ClassVar, List
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv(override=True)

# Define application paths
ROOT_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = os.getenv("DATA_DIR", str(ROOT_DIR / "data"))
CLASS_HIERARCHY_FILE = "class_hierarchy.json"
CLASS_HIERARCHY_PATH = os.getenv("CLASS_HIERARCHY_PATH", str(ROOT_DIR / "data" / CLASS_HIERARCHY_FILE))

class Settings(BaseSettings):
    # Database configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "digital_twins_db")
    
    # API configuration
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Digital Twin Platform")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Security configuration - defined as a ClassVar to bypass Pydantic validation
    ALLOW_ORIGINS: ClassVar[List[str]] = []
    
    # Dashboard configuration
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8050"))
    
    # File paths
    DATA_DIR: str = DATA_DIR
    CLASS_HIERARCHY_PATH: str = CLASS_HIERARCHY_PATH
    
    # Set ALLOW_ORIGINS as a class variable after initialization
    @model_validator(mode='after')
    def set_allow_origins(self):
        type(self).ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()