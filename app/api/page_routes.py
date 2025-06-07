from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Return login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/achievements", response_class=HTMLResponse)
def achievements_page(request: Request):
    """Return achievements page"""
    return templates.TemplateResponse("achievements.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    """Return dashboard page"""
    return templates.TemplateResponse("achievements.html", {"request": request})