from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.health import router as health_router
from app.api.api_connections import router as api_connections_router
from database.db_setup import engine
from app.models.health import Base as HealthBase
from app.models.user import Base as UserBase
from app.api.auth import router as auth_router
from app.services.auth import get_current_user
import os

# Create directories if they don't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Create database tables
HealthBase.metadata.create_all(bind=engine)
UserBase.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Health & Finance Dashboard",
              description="API to track health and financial data",
              version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Add routers - TUTAJ NAJWAŻNIEJSZA ZMIANA
app.include_router(health_router, prefix="/api/health", tags=["health"])  # Zmieniony prefix
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_connections_router, prefix="/api/connections", tags=["api_connections"])  # Zmieniony prefix

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Redirect to login page if not authenticated, otherwise to dashboard
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Display login page
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Display registration page
    """
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    """
    Display health dashboard
    """
    return templates.TemplateResponse("health_dashboard.html", {"request": request})

@app.get("/connections", response_class=HTMLResponse)
async def connections_page(request: Request):
    """
    Display API connections management page
    """
    return templates.TemplateResponse("connections.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)