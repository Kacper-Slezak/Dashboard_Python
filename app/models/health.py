from typing import List, Dict, Any

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.db_setup import Base

class HeartRate(Base):
    __tablename__ = 'heart_rate'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    bpm_value = Column(Integer, nullable=False)

    user = relationship('User', back_populates='heart_rates')


class Sleep(Base):
    __tablename__ = 'sleep'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    sleep_value = Column(Integer, nullable=False)

    user = relationship('User', back_populates='sleep')


class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    activity_type = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    calories = Column(Integer, nullable=False)

    user = relationship('User', back_populates='activity')

class StepData(BaseModel):
    steps: int

class DashboardResponse(BaseModel):
    steps: List[Dict[str, Any]]
    sleep: List[Dict[str, Any]]
    heart_rate: List[Dict[str, Any]]
    metrics: Dict[str, float]

    class Config:
        json_schema_extra = {
            "example": {
                "steps": [{"date": "2023-01-01", "steps": 8500}],
                "sleep": [{"date": "2023-01-01", "duration": 7.5}],
                "heart_rate": [{"timestamp": "2023-01-01T08:00:00", "bpm": 72}],
                "metrics": {"avg_steps": 7850, "avg_sleep": 7.2}
            }
        }