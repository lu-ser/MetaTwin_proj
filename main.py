from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.router import router
from app.db.database import connect_to_mongo, close_mongo_connection
from app.config import settings, ROOT_DIR, DATA_DIR
import uvicorn
import os
from pathlib import Path

# Make sure the data directory exists
data_dir = Path(DATA_DIR)
data_dir.mkdir(exist_ok=True)

# Copy the class_hierarchy.json file if it doesn't exist already
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure StaticFiles to serve static files
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "app" / "static")), name="static")

# Configure Jinja2 Templates
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))

# Connect the APIs to the correct route
app.include_router(router, prefix="/api/v1")

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": f"/api/v1/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )