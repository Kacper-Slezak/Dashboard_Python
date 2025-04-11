from fastapi import FastAPI
from app.api.health import router as health_router
# from app.api.finance import router as finance_router  # Odkomentuj, gdy zaimplementujesz
from database.db_setup import engine
from app.models.health import Base

# Tworzenie tabel w bazie danych
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Health API",
              description="API do śledzenia danych zdrowotnych i finansowych",
              version="0.1.0")

# Dodawanie routerów
app.include_router(health_router, prefix="/api", tags=["health"])
# app.include_router(finance_router, prefix="/api", tags=["finance"])  # Odkomentuj, gdy zaimplementujesz

@app.get("/")
def read_root():
    return {"message": "Witaj w Personal Health API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)