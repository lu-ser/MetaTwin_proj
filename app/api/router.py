from fastapi import APIRouter
from .endpoints import devices, digital_twins, sensors, users

router = APIRouter()

router.include_router(devices.router, prefix="/devices", tags=["Devices"])
router.include_router(digital_twins.router, prefix="/digital-twins", tags=["Digital Twins"])
router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
router.include_router(users.router, prefix="/users", tags=["Users"])