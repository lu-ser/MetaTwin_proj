# app/db/crud.py
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Dict, List, Any, Optional
from .database import get_database

# Funzioni CRUD base per collezioni
async def create_document(collection_name: str, document: Dict[str, Any]) -> str:
    """Crea un nuovo documento nella collezione specificata"""
    db = get_database()
    collection = db[collection_name]
    result = await collection.insert_one(document)
    return str(result.inserted_id)

async def get_document(collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Recupera un documento dalla collezione in base all'ID"""
    db = get_database()
    collection = db[collection_name]
    document = await collection.find_one({"id": document_id})
    return document

async def update_document(collection_name: str, document_id: str, update_data: Dict[str, Any]) -> bool:
    """Aggiorna un documento esistente"""
    db = get_database()
    collection = db[collection_name]
    result = await collection.update_one(
        {"id": document_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_document(collection_name: str, document_id: str) -> bool:
    """Elimina un documento dalla collezione"""
    db = get_database()
    collection = db[collection_name]
    result = await collection.delete_one({"id": document_id})
    return result.deleted_count > 0

async def list_documents(collection_name: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Elenca documenti dalla collezione, opzionalmente filtrando per query"""
    db = get_database()
    collection = db[collection_name]
    
    if query is None:
        query = {}
        
    cursor = collection.find(query)
    documents = await cursor.to_list(length=100)  # Limita a 100 documenti
    return documents