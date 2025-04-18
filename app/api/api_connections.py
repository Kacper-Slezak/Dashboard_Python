# app/api/api_connections.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from app.services.auth import get_current_user
from app.models.user import User
from database.db_setup import get_db
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
import secrets
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from database.db_setup import Base


# Definicje modeli dla połączeń API
class ApiConnection(Base):
    __tablename__ = 'api_connections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    provider = Column(String, nullable=False)  # np. 'google_fit', 'strava', itp.
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    connection_data = Column(JSON, nullable=True)  # dodatkowe dane konfiguracyjne
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacja z modelem User zostanie dodana później do modelu User


# Schematy Pydantic
class ApiConnectionCreate(BaseModel):
    provider: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    connection_data: Optional[Dict[str, Any]] = None


class ApiConnectionResponse(BaseModel):
    id: int
    provider: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Router dla połączeń API
router = APIRouter(
    prefix="/api-connections",
    tags=["API Connections"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[ApiConnectionResponse])
async def get_user_api_connections(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Pobiera listę wszystkich połączeń API dla zalogowanego użytkownika.
    """
    connections = db.query(ApiConnection).filter(
        ApiConnection.user_id == current_user.id
    ).all()

    return connections


@router.post("/", response_model=ApiConnectionResponse)
async def create_api_connection(
        connection_data: ApiConnectionCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Tworzy nowe połączenie API dla zalogowanego użytkownika.
    """
    # Sprawdzenie, czy połączenie z tym dostawcą już istnieje
    existing_connection = db.query(ApiConnection).filter(
        ApiConnection.user_id == current_user.id,
        ApiConnection.provider == connection_data.provider
    ).first()

    if existing_connection:
        # Aktualizacja istniejącego połączenia
        for key, value in connection_data.dict().items():
            if value is not None:
                setattr(existing_connection, key, value)

        existing_connection.updated_at = datetime.now()
        existing_connection.is_active = True

        db.commit()
        db.refresh(existing_connection)
        return existing_connection

    # Utworzenie nowego połączenia
    new_connection = ApiConnection(
        user_id=current_user.id,
        **connection_data.dict()
    )

    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)

    return new_connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_connection(
        connection_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Usuwa połączenie API dla zalogowanego użytkownika.
    """
    connection = db.query(ApiConnection).filter(
        ApiConnection.id == connection_id,
        ApiConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Połączenie API nie zostało znalezione"
        )

    db.delete(connection)
    db.commit()

    return None


# Funkcja do inicjalizacji połączenia z Google Fit
@router.post("/google-fit/auth", response_model=Dict[str, Any])
async def initialize_google_fit_auth(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """
    Inicjalizuje proces autoryzacji z Google Fit.

    Generuje URL, na który użytkownik musi przejść, aby zalogować się do Google
    i udzielić zgody na dostęp do danych z Google Fit.
    """
    # Generowanie stanu dla zabezpieczenia CSRF
    state = secrets.token_urlsafe(16)

    # Adres zwrotny, na który Google przekieruje użytkownika po autoryzacji
    # Powinien być skonfigurowany w Google Cloud Console
    redirect_uri = f"{request.base_url}api-connections/google-fit/callback"

    # Zakres uprawnień dla Google Fit
    scopes = [
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.sleep.read",
        "https://www.googleapis.com/auth/fitness.heart_rate.read",
        "https://www.googleapis.com/auth/fitness.body.read",
        "https://www.googleapis.com/auth/fitness.location.read"
    ]

    # URL autoryzacji Google
    auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={redirect_uri}&scope={'%20'.join(scopes)}&state={state}&access_type=offline&prompt=consent"

    return {
        "auth_url": auth_url,
        "state": state,
        "message": "Przejdź na podany URL, aby zalogować się do Google Fit"
    }


@router.get("/google-fit/callback")
async def google_fit_callback(
        code: str,
        state: str,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Obsługuje callback od Google po autoryzacji.

    Wymienia kod autoryzacyjny na tokeny dostępu i odświeżania.
    """
    # TODO: Weryfikacja stanu dla zabezpieczenia przed atakami CSRF

    # Adres API Google do wymiany kodu
    token_url = "https://oauth2.googleapis.com/token"

    # Parametry potrzebne do wymiany kodu na tokeny
    redirect_uri = f"{request.base_url}api-connections/google-fit/callback"

    # Użycie zewnętrznej biblioteki do wymiany kodu (np. requests)
    # W rzeczywistym kodzie tutaj należałoby użyć biblioteki HTTP
    # do wysłania żądania POST do Google

    # Symulacja odpowiedzi od Google
    # W prawdziwym kodzie tutaj byłaby odpowiedź z API Google
    token_response = {
        "access_token": "sample_access_token",
        "refresh_token": "sample_refresh_token",
        "expires_in": 3600  # sekundy
    }

    # Zapisanie tokenów w sesji lub przekazanie ich do innego endpointu
    # do zapisania w bazie danych

    # Przekierowanie użytkownika do strony z informacją o sukcesie
    return {"message": "Połączenie z Google Fit zostało ustanowione pomyślnie!"}

# Dodanie obsługi innych zewnętrznych API (np. Strava, Fitbit) w podobny sposób