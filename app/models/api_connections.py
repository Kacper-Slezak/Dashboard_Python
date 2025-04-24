# app/models/api_connection.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db_setup import Base


class ApiConnection(Base):
    __tablename__ = 'api_connections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)  # Fixed to match user table name
    provider = Column(String(50), nullable=False)  # np. 'google_fit', 'strava', itp.

    # Access tokens
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)

    # Additional connection data (state, etc.)
    connection_data = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Define the relationship from this side
    user = relationship("User", back_populates="api_connections")