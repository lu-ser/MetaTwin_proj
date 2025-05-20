from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pathlib import Path

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Definizione dei percorsi dell'applicazione
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = os.getenv("DATA_DIR", str(ROOT_DIR / "data"))
CLASS_HIERARCHY_PATH = os.getenv("CLASS_HIERARCHY_PATH", str(Path(DATA_DIR) / "class_hierarchy.json"))

class Settings(BaseSettings):
    # Configurazione Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "digital_twins_db")
    
    # Configurazione API
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Digital Twin Platform")
    
    # Configurazione Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Configurazione Sicurezza
    ALLOW_ORIGINS: list = os.getenv("ALLOW_ORIGINS", "*").split(",")
    
    # Configurazione Dashboard
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8050"))
    
    # Percorsi dei file
    DATA_DIR: str = DATA_DIR
    CLASS_HIERARCHY_PATH: str = CLASS_HIERARCHY_PATH

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()