from fastapi import FastAPI, HTTPException, Request, APIRouter, Path
from pydantic import BaseModel, Field, validator, ValidationError
from pymongo import MongoClient
from typing import List, Dict
import random
import json
import uuid
from bson import ObjectId


app = FastAPI()

class Attribute(BaseModel):
    value: float
    unit_measure: str = ""

class DeviceModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    attributes: Dict[str, Attribute]

@validator('attributes', pre=True, each_item=True)
def unpack_attributes(cls, v):
    if isinstance(v, dict) and 'value' in v and 'unit_measure' in v:
        return v
    elif isinstance(v, (int, float)):
        return {'value': v, 'unit_measure': ''}
    raise ValueError('Invalid attribute format')
class MeasureModel(BaseModel):
    attribute_name: str
    value: float
    unit_measure: str = ""

class UserModel(BaseModel):
    id: str = Field(alias='_id')
    name: str
    devices: List[DeviceModel]
    class Config:
        allow_population_by_field_name = True
class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Genera automaticamente un ID unico
    name: str
    attributes: Dict[str, Attribute] = {}

    def add_attribute(self, attr_name: str, specs: dict):
        if 'min' in specs and 'max' in specs:
            mean = specs.get('mean', (specs['min'] + specs['max']) / 2)
            value = round(random.gauss(mean, (specs['max'] - specs['min']) / 6), 2)
            self.attributes[attr_name] = {
                "value": value,
                "unit_measure": specs.get('unitMeasure', '')
            }

def prepare_device_data(device_data):
    if 'attributes' in device_data:
        for key, attr in device_data['attributes'].items():
            if isinstance(attr, dict) and 'value' in attr and 'unit_measure' in attr:
                continue
            elif isinstance(attr, (int, float)):
                device_data['attributes'][key] = {'value': attr, 'unit_measure': ''}
    return device_data

# Connessione al client MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['user_data']
users = db['users']

@app.post("/users/", tags=["Users"])
def create_user():
    user_id = str(random.randint(10 ** 14, 10 ** 15 - 1))
    while users.find_one({"_id": user_id}):
        user_id = str(random.randint(10 ** 14, 10 ** 15 - 1))

    with open('class_hierarchy.json', 'r') as file:
        data = json.load(file)

    all_devices = [Device(name=key) for key, value in data.items() if not value.get('superclass')]
    num_devices = random.randint(1, len(all_devices))
    selected_devices = random.sample(all_devices, num_devices)

    for device in selected_devices:
        for key, value in data.items():
            if 'superclass' in value and device.name in value['superclass']:
                if isinstance(value, dict) and 'min' in value and 'max' in value:
                    mean = value.get('mean', (value['min'] + value['max']) / 2)
                    device_value = round(random.gauss(mean, (value['max'] - value['min']) / 6), 2)
                    unit_measure = value.get('unitMeasure', '')  # Assicurati che sia una stringa
                    if isinstance(unit_measure, list):  # Se per qualche motivo è una lista, prendi il primo elemento
                        unit_measure = unit_measure[0] if unit_measure else ''
                    device.attributes[key] = Attribute(
                        value=device_value,
                        unit_measure=unit_measure
                    )

    user_doc = {
        "_id": user_id,
        "name": f"User{user_id}",
        "devices": [device.dict() for device in selected_devices]
    }
    users.insert_one(user_doc)
    return {"message": f"User created successfully with ID {user_id}"}


@app.get("/users/",tags=["Users"])
def retrieve_users():
    all_users = list(users.find({}, {'_id': 1, 'name': 1, 'devices': 1}))  # Includi l'_id nella risposta
    for user in all_users:
        user['_id'] = str(user['_id'])  # Assicurati che l'_id sia una stringa
    return all_users


@app.get("/users/{user_id}", tags=["Users"])
def retrieve_user(user_id: str):
    # Query direttamente con la stringa dell'ID
    user = users.find_one({"_id": user_id}, {'_id': 1, 'name': 1, 'devices': 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Assicurati che l'_id sia una stringa per compatibilità con il modello Pydantic
    user['_id'] = str(user['_id'])

    return user

@app.post("/users/{user_id}/add_device", response_model=UserModel, tags=["Devices"])
async def add_device_to_user(user_id: str, device: DeviceModel):
    user = users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prendi la lista esistente di dispositivi, o inizializzala se non esiste
    user_devices = user.get('devices', [])

    # Aggiungi il nuovo dispositivo dopo aver controllato per duplicati
    if any(d['id'] == device.id for d in user_devices):
        raise HTTPException(status_code=400, detail="Device with this ID already exists for this user")

    user_devices.append(
        device.dict(by_alias=True))  # Usa by_alias=True per garantire che gli alias dei modelli vengano usati
    users.update_one({"_id": user_id}, {"$set": {"devices": user_devices}})

    updated_user = users.find_one({"_id": user_id})
    return updated_user

@app.post("/create_custom_user/", response_model=UserModel, summary="Create a Custom User", tags=["Users"])
def create_custom_user(user: UserModel):
    if users.find_one({"_id": user.id}):
        raise HTTPException(status_code=400, detail="User already exists")

    user_dict = user.dict()
    user_dict['_id'] = user.id  # Usa il nome come ID per semplicità

    users.insert_one(user_dict)
    return user

@app.put("/users/{user_id}/devices/{device_id}", response_model=Device, tags=["Devices"])
def update_device(user_id: str, device_id: str, device_update: DeviceModel):
    # Prendi il dispositivo esistente per assicurarti di non cambiare l'ID
    existing_device = users.find_one({"_id": user_id, "devices.id": device_id}, {"devices.$": 1})
    if not existing_device:
        raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found for User {user_id}")

    # Prepara l'oggetto di aggiornamento mantenendo lo stesso ID
    device_update_dict = device_update.dict(exclude_unset=True)
    device_update_dict['id'] = device_id  # Assicura che l'ID rimanga invariato

    # Esegui l'aggiornamento
    result = users.update_one(
        {"_id": user_id, "devices.id": device_id},
        {"$set": {"devices.$": device_update_dict}}
    )

    if result.modified_count:
        updated_device = users.find_one({"_id": user_id, "devices.id": device_id}, {"devices.$": 1})
        return updated_device['devices'][0]
    else:
        raise HTTPException(status_code=404, detail="Update failed or no changes made.")


@app.post("/users/{user_id}/devices/{device_id}/measure", tags=["Devices","Measures"])
def add_measure(user_id: str, device_id: str, measure: MeasureModel):
    # Trova il dispositivo all'interno dell'utente
    user = users.find_one({"_id": user_id, f"devices.id": device_id})
    if not user:
        raise HTTPException(status_code=404, detail=f"User or device not found.")

    # Trova il dispositivo specifico
    device_index = next((index for (index, d) in enumerate(user['devices']) if d['id'] == device_id), None)
    if device_index is None:
        raise HTTPException(status_code=404, detail="Device not found.")

    # Prepara il percorso dell'attributo da aggiornare
    attribute_path = f"devices.{device_index}.attributes.{measure.attribute_name}"

    # Aggiorna o inserisci la nuova misura
    update_result = users.update_one(
        {"_id": user_id},
        {"$set": {
            f"{attribute_path}.value": measure.value,
            f"{attribute_path}.unit_measure": measure.unit_measure
        }}
    )

    if update_result.modified_count:
        return {"message": "Measurement added successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to add measurement.")
# Router per le operazioni sugli utenti
user_router = APIRouter(tags=["Utenti"])
device_router = APIRouter(tags=["Dispositivi"])
measure_router = APIRouter(tags=["Misure"])

# Registrazione dei router
app.include_router(user_router)
app.include_router(device_router)
app.include_router(measure_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
