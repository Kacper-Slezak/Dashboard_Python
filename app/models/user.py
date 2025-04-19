# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database.db_setup import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    # Relacje
    transactions = relationship('Transaction', back_populates='user')
    budgets = relationship('Budget', back_populates='user')
    heart_rates = relationship('HeartRate', back_populates='user')
    sleep = relationship('Sleep', back_populates='user')
    activity = relationship('Activity', back_populates='user')