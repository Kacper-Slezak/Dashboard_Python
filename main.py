from fastapi import FastAPI, Request, Depends, HTTPException, status, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from database.db_setup import engine
from dotenv import load_dotenv
import os

# Inicjalizacja aplikacji JAKO PIERWSZA OPERACJA
app = FastAPI(
    title="Personal Health & Finance Dashboard",
    description="API to track health and financial data",
    version="0.1.0"
)

# Konfiguracja CORS JAKO DRUGA OPERACJA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reszta importów PO UTWORZENIU APLIKACJI
from app.api.health import router as health_router
from app.api.api_connections import router as api_connections_router
from app.models.health import Base as HealthBase
from app.models.user import Base as UserBase
from app.api.auth import router as auth_router
from app.services.auth import get_current_user

load_dotenv()

# Tworzenie tabel w bazie danych
HealthBase.metadata.create_all(bind=engine)
UserBase.metadata.create_all(bind=engine)

# Konfiguracja szablonów i plików statycznych
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Dodawanie routerów
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_connections_router, tags=["api_connections"])

# Endpointy HTML
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    return templates.TemplateResponse("health_dashboard.html", {"request": request})

@app.get("/connections", response_class=HTMLResponse)
async def connections_page(request: Request):
    return templates.TemplateResponse("connections.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)