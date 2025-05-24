from fastapi import APIRouter
from app.api.endpoints import devices, digital_twins, sensors, users, auth, templates
from app.ui import views

# Create the main API router
api_router = APIRouter()

# API Endpoints
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(digital_twins.router, prefix="/digital-twins", tags=["Digital Twins"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])

# Create the main router that will include both API and UI
router = APIRouter()

# Include the API router
router.include_router(api_router)

# UI Views
router.include_router(views.router, tags=["Views"])