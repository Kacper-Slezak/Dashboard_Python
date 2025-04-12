"""
Moduł zawierający punkty końcowe API (endpointy) dla danych zdrowotnych.

Ten moduł definiuje ścieżki API dla pobierania różnych kategorii danych zdrowotnych
z Google Fit API oraz bazy danych, w tym danych o krokach, śnie i tętnie.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.health import GoogleFitServices
from app.models.health import HeartRate, Sleep, Activity
from database.db_setup import get_db
from app.services.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel
from app.services.predictions import predict_steps

# Poprawne utworzenie obiektu router
router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)


@router.get('/steps')
async def get_steps(
        current_user: User = Depends(get_current_user),
        start_date: Optional[str] = Query(None, description="Data początkowa w formacie YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Data końcowa w formacie YYYY-MM-DD")
):
    """
    Pobiera dane o krokach z określonego przedziału czasowego.

    Jeśli daty nie są podane, domyślnie zwraca dane z ostatnich 7 dni.

    Args:
        start_date: Data początkowa w formacie YYYY-MM-DD.
        end_date: Data końcowa w formacie YYYY-MM-DD.

    Returns:
        Słownik zawierający listę danych o krokach dla każdego dnia.
    """
    if start_date is None:
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=7)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    services = GoogleFitServices()
    steps_data = services.get_steps_data(start_date_obj, end_date_obj)
    return {"data": steps_data}


@router.get('/sleep')
async def get_sleep(
        start_date: Optional[str] = Query(None, description="Data początkowa w formacie YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Data końcowa w formacie YYYY-MM-DD")
):
    """
    Pobiera dane o śnie z określonego przedziału czasowego.

    Jeśli daty nie są podane, domyślnie zwraca dane z ostatnich 7 dni.

    Args:
        start_date: Data początkowa w formacie YYYY-MM-DD.
        end_date: Data końcowa w formacie YYYY-MM-DD.

    Returns:
        Słownik zawierający listę danych o śnie dla każdego dnia.
    """
    if start_date is None:
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=7)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    services = GoogleFitServices()
    sleep_data = services.get_sleep_data(start_date_obj, end_date_obj)
    return {"data": sleep_data}


@router.get('/heart/{user_id}')
async def get_heart(
        user_id: int,
        db: Session = Depends(get_db)
):
    """
    Pobiera dane o tętnie dla określonego użytkownika z bazy danych.

    Args:
        user_id: Identyfikator użytkownika.
        db: Sesja bazy danych (wstrzykiwana automatycznie).

    Returns:
        Słownik zawierający listę pomiarów tętna dla użytkownika.

    Raises:
        HTTPException: Gdy dane o tętnie nie zostały znalezione dla danego użytkownika.
    """
    heart_rates = db.query(HeartRate).filter(HeartRate.user_id == user_id).all()
    if not heart_rates:
        raise HTTPException(status_code=404, detail="Nie znaleziono danych o tętnie dla tego użytkownika")

    return {"data": [
        {
            "id": hr.id,
            "timestamp": hr.timestamp,
            "bpm_value": hr.bpm_value
        } for hr in heart_rates
    ]}


@router.get('/heart-rate')
async def get_heart_rate(
        start_date: Optional[str] = Query(None, description="Data początkowa w formacie YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Data końcowa w formacie YYYY-MM-DD")
):
    """
    Pobiera dane o tętnie z Google Fit API dla określonego przedziału czasowego.

    Jeśli daty nie są podane, domyślnie zwraca dane z ostatnich 7 dni.

    Args:
        start_date: Data początkowa w formacie YYYY-MM-DD.
        end_date: Data końcowa w formacie YYYY-MM-DD.

    Returns:
        Słownik zawierający listę danych o tętnie dla każdego dnia.
    """
    if start_date is None:
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=7)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    services = GoogleFitServices()
    heart_rate_data = services.get_heart_rate_data(start_date_obj, end_date_obj)
    return {"data": heart_rate_data}


@router.get('/activity')
async def get_activity(
        start_date: Optional[str] = Query(None, description="Data początkowa w formacie YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Data końcowa w formacie YYYY-MM-DD")
):
    """
    Pobiera dane o aktywności fizycznej z określonego przedziału czasowego.

    Jeśli daty nie są podane, domyślnie zwraca dane z ostatnich 7 dni.

    Args:
        start_date: Data początkowa w formacie YYYY-MM-DD.
        end_date: Data końcowa w formacie YYYY-MM-DD.

    Returns:
        Słownik zawierający listę danych o aktywności dla każdego dnia.
    """
    if start_date is None:
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=7)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    services = GoogleFitServices()
    activity_data = services.get_activity_data(start_date_obj, end_date_obj)
    return {"data": activity_data}


@router.get('/all')
async def get_all_health_data(
        start_date: Optional[str] = Query(None, description="Data początkowa w formacie YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Data końcowa w formacie YYYY-MM-DD"),
        format: Optional[str] = Query("json", description="Format odpowiedzi (json lub csv)")
):
    """
    Pobiera wszystkie dostępne dane zdrowotne z określonego przedziału czasowego.

    Endpoint ten agreguje dane z wszystkich źródeł zdrowotnych i zwraca je
    w wybranym formacie.

    Args:
        start_date: Data początkowa w formacie YYYY-MM-DD.
        end_date: Data końcowa w formacie YYYY-MM-DD.
        format: Format odpowiedzi - "json" (domyślnie) lub "csv".

    Returns:
        Dane zdrowotne w wybranym formacie.
    """
    if start_date is None:
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=30)  # Domyślnie ostatnie 30 dni
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    services = GoogleFitServices()
    all_data = services.get_all_health_data(start_date_obj, end_date_obj)

    if format.lower() == "csv":
        # Tutaj można dodać implementację eksportu do CSV
        return {"message": "Format CSV nie jest jeszcze zaimplementowany"}

    # Konwersja DataFrames na listy słowników
    response_data = {}
    for key, df in all_data.items():
        if not df.empty:
            # Konwertuj daty na stringi, żeby były serializowalne do JSON
            if 'date' in df.columns:
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            response_data[key] = df.to_dict('records')
        else:
            response_data[key] = []

    return {"data": response_data}

class StepData(BaseModel):
    steps: int


# Endpoint do przewidywania kroków
@router.get("/predict/steps")
def predict_steps_endpoint(days: int, steps_data: list[StepData]):
    # Przekształcanie listy obiektów StepData na listę słowników
    steps_data_list = [{"steps": data.steps} for data in steps_data]

    # Używanie funkcji predict_steps
    predicted_steps = predict_steps(steps_data_list)

    return {"predicted_steps": predicted_steps}