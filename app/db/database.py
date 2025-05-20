from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class Database:
    client: AsyncIOMotorClient = None
    
async def connect_to_mongo():
    Database.client = AsyncIOMotorClient(settings.MONGODB_URL)
    
async def close_mongo_connection():
    if Database.client:
        Database.client.close()

def get_database():
    return Database.client[settings.DATABASE_NAME]