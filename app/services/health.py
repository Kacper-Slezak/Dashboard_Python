from datetime import datetime
from app.models.health import Sleep, HeartRate, Activity
from database.db_setup import SessionLocal

db = SessionLocal()

def save_heart_rate():
    heart_rate = HeartRate(
        user_id=user_id,
        timestamp=timestamp,
        bpm_value=bpm_value
    )