# app/api/health.py
from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timedelta
from app.services.health import GoogleFitServices
from app.services.auth import get_current_user
from app.models.user import User # <-- Ważny import

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_data(
    days: int = Query(7, description="Number of days"),
    current_user: User = Depends(get_current_user)
):
    try:
        service = GoogleFitServices(user_id=current_user.id)
        data = service.get_dashboard_data(days)
        return {
            "daily_stats": data["daily_stats"],
            "charts": data["charts"]
        }
    except HTTPException as e: # Najpierw łap HTTPException
        raise e
    except Exception as e:
        print(f"Nieoczekiwany błąd w /api/health/dashboard: {e}") # Logowanie błędu
        raise HTTPException(status_code=500, detail="Wystąpił wewnętrzny błąd serwera podczas pobierania danych.")