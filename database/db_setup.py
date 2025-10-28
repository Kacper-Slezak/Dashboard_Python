from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

Base = declarative_base()


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency to get the database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()