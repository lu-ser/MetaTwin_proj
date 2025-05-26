import os
from pathlib import Path

# PythonAnywhere specific settings
ROOT_DIR = Path("/home/lser93/MetaTwin_proj")
DATA_DIR = ROOT_DIR / "data"

# MongoDB Atlas connection (già configurato)
MONGODB_URL = os.getenv("MONGODB_URL", "your_atlas_connection_string")

# Altri settings
DEBUG = False
HOST = "0.0.0.0"
PORT = 8000  # Non usato in WSGI ma manteniamo per compatibilità
PROJECT_NAME = "MetaTwin Platform"
API_PREFIX = "/api/v1"

# CORS
ALLOW_ORIGINS = ["*"]  # In produzione, specifica i domini corretti

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
DATABASE_NAME = "digital_twin_platform"

# Paths
CLASS_HIERARCHY_PATH = DATA_DIR / "class_hierarchy.json"