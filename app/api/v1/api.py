from fastapi import APIRouter
from app.api.v1 import users, devices, digital_twins, sensors, ontology, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(digital_twins.router, prefix="/digital_twins", tags=["digital_twins"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])
api_router.include_router(ontology.router, prefix="/ontology", tags=["ontology"]) 