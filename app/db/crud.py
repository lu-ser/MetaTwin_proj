# app/db/crud.py
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Dict, List, Any, Optional
from .database import get_database
from bson import ObjectId

# Funzioni CRUD base per collezioni
async def create_document(collection_name: str, document: Dict[str, Any]) -> str:
    """Crea un nuovo documento nella collezione specificata"""
    db = get_database()
    collection = db[collection_name]
    
    # Ensure document has an id field
    if "id" not in document:
        document["id"] = str(ObjectId())
    
    result = await collection.insert_one(document)
    return document["id"]

async def get_document(collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Recupera un documento dalla collezione in base all'ID"""
    db = get_database()
    collection = db[collection_name]
    
    # Try to find by id field first
    document = await collection.find_one({"id": document_id})
    
    # If not found, try _id field (for backward compatibility)
    if not document:
        try:
            document = await collection.find_one({"_id": document_id})
        except:
            pass
    
    # Convert ObjectId to string if present
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    
    return document

async def update_document(collection_name: str, document_id: str, update_data: Dict[str, Any]) -> bool:
    """Aggiorna un documento esistente"""
    db = get_database()
    collection = db[collection_name]
    
    # Try to update by id field first
    result = await collection.update_one(
        {"id": document_id},
        {"$set": update_data}
    )
    
    # If no document was modified, try _id field
    if result.modified_count == 0:
        try:
            result = await collection.update_one(
                {"_id": document_id},
                {"$set": update_data}
            )
        except:
            pass
    
    return result.modified_count > 0

async def delete_document(collection_name: str, document_id: str) -> bool:
    """Elimina un documento dalla collezione"""
    db = get_database()
    collection = db[collection_name]
    
    # Try to delete by id field first
    result = await collection.delete_one({"id": document_id})
    
    # If no document was deleted, try _id field
    if result.deleted_count == 0:
        try:
            result = await collection.delete_one({"_id": document_id})
        except:
            pass
    
    return result.deleted_count > 0

async def list_documents(collection_name: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Elenca documenti dalla collezione, opzionalmente filtrando per query"""
    db = get_database()
    collection = db[collection_name]
    
    if query is None:
        query = {}
        
    cursor = collection.find(query)
    documents = await cursor.to_list(length=100)  # Limita a 100 documenti
    
    # Convert ObjectIds to strings and ensure id field exists
    for doc in documents:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
            if "id" not in doc:
                doc["id"] = doc["_id"]
    
    return documents