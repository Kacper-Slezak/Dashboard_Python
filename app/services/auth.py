import os
from datetime import datetime, timedelta
import dotenv
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from database.db_setup import get_db

dotenv.load_dotenv()

# Poprawne odczytanie zmiennych środowiskowych z wartościami domyślnymi
SECRET_KEY = os.getenv('SECRET_KEY', 'tajny_klucz_zamienic_w_produkcji')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
# Konwersja na int z wartością domyślną w przypadku błędu
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Poprawiona ścieżka


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    # Poprawne ustawienie czasu wygaśnięcia
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nie można zweryfikować poświadczeń",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Użyj metody first() zamiast bezpośredniego filtrowania
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    # Sprawdź, czy konto jest aktywne
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Konto użytkownika jest nieaktywne",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user