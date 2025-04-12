from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.health import router as health_router
# from app.api.finance import router as finance_router  # Odkomentuj, gdy zaimplementujesz
from database.db_setup import engine
from app.models.health import Base as HealthBase
from app.models.user import Base as UserBase
from app.api.auth import router as auth_router
import os

# Tworzenie katalogów, jeśli nie istnieją
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Tworzenie tabel w bazie danych
HealthBase.metadata.create_all(bind=engine)
UserBase.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Health & Finance Dashboard",
              description="API do śledzenia danych zdrowotnych i finansowych",
              version="0.1.0")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inicjalizacja szablonów
templates = Jinja2Templates(directory="templates")

# Dodawanie routerów
app.include_router(health_router, prefix="/api", tags=["health"])
# app.include_router(finance_router, prefix="/api", tags=["finance"])  # Odkomentuj, gdy zaimplementujesz
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("health_dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request):
    return templates.TemplateResponse("health_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)