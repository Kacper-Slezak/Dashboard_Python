# app/models/__init__.py
from database.db_setup import Base

# Importuj wszystkie swoje modele, aby zarejestrować je w Base
from .user import User
from .health import HeartRate, Sleep, Activity
from .transaction import Transaction
from .api_connections import ApiConnection