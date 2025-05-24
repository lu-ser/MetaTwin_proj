# app/api/endpoints/templates.py
from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from app.models.device_template import DeviceTemplate, AttributeDefinition, AttributeType
from app.db.crud import create_document, get_document, update_document, delete_document, list_documents
from app.api.auth_service import get_current_active_user
from app.ontology.manager import OntologyManager

router = APIRouter()

@router.post("/", response_model=DeviceTemplate, status_code=201)
async def create_device_template(
    template: DeviceTemplate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new device template
    """
    # Set current user as owner if not already specified
    if not template.owner_id:
        template.owner_id = current_user["id"]
    
    # Verify that the current user can create a template for the specified owner
    if template.owner_id != current_user["id"]:
        # You could implement more advanced role checks here (e.g., admin)
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to create templates for other users"
        )
    
    # Save the template in the database
    template_dict = template.dict()
    await create_document("device_templates", template_dict)
    
    # Get the complete document of the saved template
    saved_template = await get_document("device_templates", template.id)
    return saved_template

@router.get("/", response_model=List[DeviceTemplate])
async def list_device_templates(
    owner_id: Optional[str] = None,
    is_ontology_based: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get all device templates, optionally filtering by owner or type"""
    query = {}
    
    # If an owner_id is specified
    if owner_id:
        query["owner_id"] = owner_id
    
    # If an ontology filter is specified
    if is_ontology_based is not None:
        query["is_ontology_based"] = is_ontology_based
    
    templates = await list_documents("device_templates", query)
    return templates

@router.get("/{template_id}", response_model=DeviceTemplate)
async def get_device_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get a specific device template by ID"""
    template = await get_document("device_templates", template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template

@router.put("/{template_id}", response_model=DeviceTemplate)
async def update_device_template(
    template_id: str, 
    template_update: DeviceTemplate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update an existing device template"""
    existing_template = await get_document("device_templates", template_id)
    if not existing_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Verify that the current user can modify this template
    if existing_template.get("owner_id") != current_user["id"]:
        # You could implement more advanced role checks here (e.g., admin)
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to modify this template"
        )
    
    # Prepare the update data
    update_data = template_update.dict(exclude_unset=True)
    
    # Update the template
    await update_document("device_templates", template_id, update_data)
    updated_template = await get_document("device_templates", template_id)
    
    return updated_template

@router.delete("/{template_id}", status_code=204)
async def delete_device_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Delete a specific device template"""
    template = await get_document("device_templates", template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Verify that the current user can delete this template
    if template.get("owner_id") != current_user["id"]:
        # You could implement more advanced role checks here (e.g., admin)
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to delete this template"
        )
    
    # Check if there are devices using this template
    devices_with_template = await list_documents("devices", {"template_id": template_id})
    if devices_with_template:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete template: it is used by {len(devices_with_template)} devices"
        )
    
    await delete_document("device_templates", template_id)
    return None

@router.post("/from-ontology", response_model=DeviceTemplate)
async def create_template_from_ontology(
    sensor_type: str = Body(..., embed=True),
    name: Optional[str] = Body(None),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Create a template based on a specific ontology type"""
    ontology = OntologyManager()
    
    # Verify that the sensor exists in the ontology
    sensor_details = ontology.get_sensor_details(sensor_type)
    if not sensor_details:
        raise HTTPException(
            status_code=404,
            detail=f"Sensor type '{sensor_type}' not found in the ontology"
        )
    
    # Create the template with parameters from the ontology sensor
    template_name = name if name else f"Template from {sensor_type}"
    
    # Build attributes from the ontology sensor
    attributes = {}
    
    # Add the main sensor attribute
    min_val = sensor_details.get("min")
    max_val = sensor_details.get("max")
    
    attributes[sensor_type] = AttributeDefinition(
        name=sensor_type,
        type=AttributeType.NUMBER,
        unit_measure=sensor_details.get("unit_measure", ""),
        description=f"Value of {sensor_type} sensor",
        constraints={"min_value": min_val, "max_value": max_val} if min_val is not None and max_val is not None else None
    )
    
    template = DeviceTemplate(
        name=template_name,
        description=f"Template automatically generated for sensor type {sensor_type}",
        attributes=attributes,
        owner_id=current_user["id"],
        is_ontology_based=True,
        metadata={"source_ontology_type": sensor_type}
    )
    
    # Save the template in the database
    template_dict = template.dict()
    await create_document("device_templates", template_dict)
    
    # Get the complete document of the saved template
    saved_template = await get_document("device_templates", template.id)
    return saved_template 