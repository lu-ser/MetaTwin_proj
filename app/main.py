from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router
from app.db.database import connect_to_mongo, close_mongo_connection
from app.config import settings, ROOT_DIR, DATA_DIR
import uvicorn
import os
from pathlib import Path

# Assicurati che la directory dei dati esista
data_dir = Path(DATA_DIR)
data_dir.mkdir(exist_ok=True)

# Copia il file class_hierarchy.json se non esiste già
ontology_file = Path(settings.CLASS_HIERARCHY_PATH)
if not ontology_file.exists():
    import shutil
    src_file = ROOT_DIR / "class_hierarchy.json"
    if src_file.exists():
        shutil.copy(src_file, ontology_file)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    debug=settings.DEBUG
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Collega le API
app.include_router(router, prefix=settings.API_PREFIX)

# Eventi di startup e shutdown
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {
        "message": f"Benvenuto in {settings.PROJECT_NAME} API",
        "docs": f"{settings.API_PREFIX}/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )