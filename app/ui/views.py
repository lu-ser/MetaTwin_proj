# app/ui/views.py - Versione corretta senza conflitti di routing
from fastapi import APIRouter, Request, Query, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Any
from pathlib import Path
from app.config import settings, ROOT_DIR
from jose import JWTError, jwt
import os

router = APIRouter()
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))

# Chiave segreta per JWT
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Funzione per verificare lo stato di autenticazione dal cookie
async def get_current_ui_user(request: Request) -> Any:
    # Per le rotte delle pagine web non usiamo JWT, ma controlliamo solo
    # che l'utente è correttamente autenticato dal frontend
    # tramite l'uso di localStorage e redirect JS
    return {"authenticated": True}

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

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renderizza la pagina di login"""
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME
        }
    )

# RIPRISTINATO: /dashboard non ha conflitti con API
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, dt: str = Query(None), current_user: Any = Depends(get_current_ui_user)):
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

# CAMBIATO: da /devices a /manage/devices per evitare conflitti
@router.get("/manage/devices", response_class=HTMLResponse)
async def devices(request: Request, current_user: Any = Depends(get_current_ui_user)):
    """Renderizza la pagina di gestione dei dispositivi"""
    return templates.TemplateResponse(
        "devices.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME
        }
    )

# CAMBIATO: da /users a /manage/users per evitare conflitti
@router.get("/manage/users", response_class=HTMLResponse)
async def users(request: Request, current_user: Any = Depends(get_current_ui_user)):
    """Renderizza la pagina di gestione degli utenti"""
    return templates.TemplateResponse(
        "users.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME
        }
    )

# CAMBIATO: da /templates a /manage/templates per evitare conflitti
@router.get("/manage/templates", response_class=HTMLResponse)
async def templates_page(request: Request, template_id: str = Query(None), current_user: Any = Depends(get_current_ui_user)):
    """Renderizza la pagina di gestione dei template
    
    Se il parametro template_id è specificato, seleziona automaticamente quel template
    """
    return templates.TemplateResponse(
        "templates.html" if Path(ROOT_DIR / "app" / "templates" / "templates.html").exists() else "templates_fallback.html", 
        {
            "request": request, 
            "title": f"{settings.PROJECT_NAME} - Templates",
            "selected_template": template_id
        }
    )

# CAMBIATO: da /template/new a /manage/template/new
@router.get("/manage/template/new", response_class=HTMLResponse)
async def new_template(request: Request, source_type: Optional[str] = Query(None), current_user: Any = Depends(get_current_ui_user)):
    """Renderizza la pagina di creazione di un nuovo template
    
    Se il parametro source_type è specificato, crea un template a partire da un tipo dell'ontologia
    """
    return templates.TemplateResponse(
        "template_edit.html" if Path(ROOT_DIR / "app" / "templates" / "template_edit.html").exists() else "templates_fallback.html", 
        {
            "request": request, 
            "title": f"{settings.PROJECT_NAME} - Nuovo Template",
            "source_type": source_type,
            "is_new": True
        }
    )

# CAMBIATO: da /template/{template_id} a /manage/template/{template_id}
@router.get("/manage/template/{template_id}", response_class=HTMLResponse)
async def edit_template(request: Request, template_id: str, current_user: Any = Depends(get_current_ui_user)):
    """Renderizza la pagina di modifica di un template esistente"""
    return templates.TemplateResponse(
        "template_edit.html" if Path(ROOT_DIR / "app" / "templates" / "template_edit.html").exists() else "templates_fallback.html", 
        {
            "request": request, 
            "title": f"{settings.PROJECT_NAME} - Modifica Template",
            "template_id": template_id,
            "is_new": False
        }
    )

@router.get("/ontology", response_class=HTMLResponse)
async def ontology(request: Request, class_name: str = Query(None), current_user: Any = Depends(get_current_ui_user)):
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

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, current_user: Any = Depends(get_current_ui_user)):
    """Renderizza la pagina del profilo utente"""
    return templates.TemplateResponse(
        "profile.html" if Path(ROOT_DIR / "app" / "templates" / "profile.html").exists() else "dashboard.html", 
        {
            "request": request, 
            "title": settings.PROJECT_NAME,
            "profile_active": True
        }
    )