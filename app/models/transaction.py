# app/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db_setup import Base
from datetime import datetime


class Transaction(Base):
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Relationship
    user = relationship("User", back_populates="transactions")
