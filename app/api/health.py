from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.services.health import GoogleFitServices
from app.models.health import HeartRate, Sleep, Activity
from database.db_setup import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@router.get('/health/steps')
def get_steps(start_date: str = None, end_date: str = None):
    """
    Pobiera dane o krokach z określonego czasu
    """
    if start_date is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    services = GoogleFitServices()
    steps_data = services.get_steps_data(start_date, end_date)
    return {"data": steps_data}

@router.get('/health/sleep')
def get_sleep(start_date: str = None, end_date: str = None):
    """
    Pobiera dane o snie z określonego przedzizału czasowego
    :param start_date: start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

    :param end_date:end_date_obj = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
    :return:{"data": sleep_data}
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    services = GoogleFitServices()
    sleep_data = services.get_sleep_data(start_date, end_date)
    return {"data": sleep_data}

@router.get('/health/heart/{user_id}')
def get_heart(user_id: int, db: Session = Depends(get_db)):
    """
    Pobiera dane apropo pracy serca
    :param user_id: int - user id
    :param db: session - database session
    :return: data - dict - heart
    """
    heart_rates = db.query(HeartRate).filter(HeartRate.user_id == user_id).all()
    if not heart_rates:
            raise HTTPException(status_code=404, detail="Heart rate not found")

    return {"data": [
        {
            "id": hr.id,
            "timestamp": hr.timestamp,
            "bpm_value": hr.bpm_value
        }for hr in heart_rates
    ]}