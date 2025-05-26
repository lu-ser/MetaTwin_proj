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
    src_file = ROOT_DIR / "data" / "class_hierarchy.json"
    if src_file.exists():
        shutil.copy(src_file, ontology_file)
    else:
        print(f"Warning: Could not find source file at {src_file}")
        print(f"Looking for class_hierarchy.json in: {ROOT_DIR}")
        # Try to find it in the root directory
        alt_src_file = ROOT_DIR / "class_hierarchy.json"
        if alt_src_file.exists():
            shutil.copy(alt_src_file, ontology_file)
            print(f"Copied from {alt_src_file} instead")
        else:
            print(f"Error: Could not find class_hierarchy.json in {ROOT_DIR}")

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
    # Print debug information
    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"CLASS_HIERARCHY_PATH: {settings.CLASS_HIERARCHY_PATH}")
    print(f"File exists: {Path(settings.CLASS_HIERARCHY_PATH).exists()}")
    
    # Check if running in PythonAnywhere environment
    is_pythonanywhere = "PYTHONANYWHERE_DOMAIN" in os.environ
    
    # Use default port if in PythonAnywhere, otherwise use the configured port
    port = 8000 if is_pythonanywhere else settings.PORT
    
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=port, 
        reload=settings.DEBUG
    )