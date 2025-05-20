# app/ui/views.py
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.config import settings, ROOT_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Renderizza la homepage"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME
        }
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, dt: str = Query(None)):
    """Renderizza la dashboard dei Digital Twins
    
    Se il parametro dt è specificato, seleziona automaticamente quel Digital Twin
    """
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME,
            "selected_dt": dt
        }
    )

@router.get("/devices", response_class=HTMLResponse)
async def devices(request: Request):
    """Renderizza la pagina di gestione dei dispositivi"""
    return templates.TemplateResponse(
        "devices.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME
        }
    )

@router.get("/ontology", response_class=HTMLResponse)
async def ontology(request: Request, class_name: str = Query(None)):
    """Renderizza la pagina di visualizzazione dell'ontologia
    
    Se il parametro class_name è specificato, seleziona automaticamente quella classe
    """
    return templates.TemplateResponse(
        "ontology.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME,
            "selected_class": class_name
        }
    )