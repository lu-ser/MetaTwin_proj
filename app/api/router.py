from fastapi import APIRouter
from app.api.endpoints import devices, digital_twins, sensors, users
from app.ui import views

router = APIRouter()

# API Endpoints
router.include_router(devices.router, prefix="/devices", tags=["Devices"])
router.include_router(digital_twins.router, prefix="/digital-twins", tags=["Digital Twins"])
router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
router.include_router(users.router, prefix="/users", tags=["Users"])

# UI Views
router.include_router(views.router, tags=["Views"])