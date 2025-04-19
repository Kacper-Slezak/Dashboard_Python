# app/api/api_connections.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Query
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session, relationship
from starlette.responses import RedirectResponse

from app.services.auth import get_current_user
from app.models.user import User
from database.db_setup import get_db
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from database.db_setup import Base
import requests

load_dotenv()


# Konfiguruj logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Utwórz handler dla konsoli
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Format logów
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Dodaj handler do logera
logger.addHandler(console_handler)

# Definicje modeli dla połączeń API
class ApiConnection(Base):
    __tablename__ = 'api_connections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    provider = Column(String, nullable=False)  # np. 'google_fit', 'strava', itp.
    user = relationship("User", back_populates="api_connections")
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
        from_attributes = True


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


@router.post("/google-fit/auth", response_model=Dict[str, Any])
async def initialize_google_fit_auth(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        from dotenv import load_dotenv
        load_dotenv()

        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        if not redirect_uri:
            raise HTTPException(500, detail="Brak konfiguracji GOOGLE_REDIRECT_URI")

        # POPRAWIONE: Zamknięcie nawiasów dla Flow.from_client_config
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=[
                "https://www.googleapis.com/auth/fitness.activity.read",
                "https://www.googleapis.com/auth/fitness.sleep.read",
                "https://www.googleapis.com/auth/fitness.heart_rate.read"
            ],
            redirect_uri=redirect_uri  # Tutaj zamykamy nawias
        )  # <--- BRAKUJĄCY NAWIAS

        # POPRAWIONE: Użyj zmiennej 'state' z authorization_url
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true"
        )

        # ZAPIS STANU: Użyj 'state' z powyższego wywołania
        existing_connection = db.query(ApiConnection).filter(
            ApiConnection.user_id == current_user.id,
            ApiConnection.provider == "google_fit"
        ).first()

        connection_data = {
            "auth_state": state,  # Używamy 'state' z authorization_url
            "redirect_uri": redirect_uri
        }

        if existing_connection:
            existing_connection.connection_data = connection_data
            existing_connection.updated_at = datetime.now()
        else:
            new_connection = ApiConnection(
                user_id=current_user.id,
                provider="google_fit",
                connection_data=connection_data
            )
            db.add(new_connection)
        db.commit()

        return {"auth_url": authorization_url}

    except Exception as e:
        logger.error(f"Auth error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=f"Błąd inicjalizacji: {str(e)}")


@router.get("/google-fit/callback", name="google_fit_callback")
async def google_fit_callback(
        code: str = Query(...),
        state: str = Query(...),
        db: Session = Depends(get_db)
):
    try:
        # Poprawione zapytanie dla SQLite z użyciem json_extract
        from sqlalchemy import func

        connection = db.query(ApiConnection).filter(
            func.json_extract(ApiConnection.connection_data, '$.auth_state') == state
        ).first()

        if not connection:
            logger.error(f"Nie znaleziono połączenia dla stanu: {state}")
            return RedirectResponse(url="/connections?error=invalid_state")

        # Weryfikacja konfiguracji
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            logger.critical("Brakujące zmienne środowiskowe Google")
            return RedirectResponse(url="/connections?error=config_error")

        # Wymiana kodu na token
        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        response = requests.post("https://oauth2.googleapis.com/token", data=token_data)

        if response.status_code != 200:
            logger.error(f"Google API error: {response.status_code} - {response.text}")
            return RedirectResponse(url="/connections?error=google_api_failure")

        token_json = response.json()

        # Aktualizacja danych połączenia
        connection.tokens = {
            "access_token": token_json.get("access_token"),
            "refresh_token": token_json.get("refresh_token"),
            "expires_at": datetime.now() + timedelta(seconds=token_json.get("expires_in", 3600))
        }
        connection.is_active = True
        connection.updated_at = datetime.now()

        db.commit()

        return RedirectResponse(url="/connections?success=google_fit_connected")

    except Exception as e:
        logger.error(f"Critical callback error: {str(e)}", exc_info=True)
        return RedirectResponse(url="/connections?error=internal_error")