from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.router import router
from app.db.database import connect_to_mongo, close_mongo_connection
from app.config import settings, ROOT_DIR, DATA_DIR
import uvicorn
import os
import sys
import socket
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

def is_port_in_use(port, host='0.0.0.0'):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def find_free_port(start_port=8000, max_attempts=10):
    """Find a free port starting from start_port."""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return None

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
    
    # Check for command line argument for port
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    # Check if port is in use
    if is_port_in_use(port):
        print(f"ERROR: Port {port} is already in use!")
        
        # Try to find a free port
        free_port = find_free_port(port + 1)
        if free_port:
            print(f"Would you like to use port {free_port} instead? (y/n)")
            response = input().strip().lower()
            if response == 'y':
                port = free_port
            else:
                print("To kill the process using the port, run one of these commands:")
                if os.name == 'posix':  # Linux/Mac
                    print(f"    sudo lsof -i :{port} | grep LISTEN")
                    print(f"    sudo kill -9 <PID>")
                else:  # Windows
                    print(f"    netstat -ano | findstr :{port}")
                    print(f"    taskkill /F /PID <PID>")
                sys.exit(1)
        else:
            print("Could not find a free port. To kill the process using the port, run one of these commands:")
            if os.name == 'posix':  # Linux/Mac
                print(f"    sudo lsof -i :{port} | grep LISTEN")
                print(f"    sudo kill -9 <PID>")
            else:  # Windows
                print(f"    netstat -ano | findstr :{port}")
                print(f"    taskkill /F /PID <PID>")
            sys.exit(1)
    
    print(f"Starting server on port {port}...")
    try:
        uvicorn.run(
            "main:app", 
            host=settings.HOST, 
            port=port, 
            reload=settings.DEBUG
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"ERROR: Port {port} is already in use!")
            print("To kill the process using the port, run one of these commands:")
            if os.name == 'posix':  # Linux/Mac
                print(f"    sudo lsof -i :{port} | grep LISTEN")
                print(f"    sudo kill -9 <PID>")
            else:  # Windows
                print(f"    netstat -ano | findstr :{port}")
                print(f"    taskkill /F /PID <PID>")
        else:
            raise