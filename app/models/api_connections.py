from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()


class ApiConnection(Base):
    __tablename__ = "api_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Poprawiona nazwa tabeli
    user = relationship("User", back_populates="api_connections")  # Zakładając, że masz tabelę users
    provider = Column(String(50))  # np. "google_fit"
    connection_data = Column(JSON)  # Przechowuje state, redirect_uri itp.
    tokens = Column(JSON)  # Przechowuje access_token, refresh_token, expires_at
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, onupdate=datetime.now())