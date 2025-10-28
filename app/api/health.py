from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timedelta
from app.services.health import GoogleFitServices
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_data(
    days: int = Query(7, description="Number of days"),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = GoogleFitServices(user_id=current_user.id)
        data = service.get_dashboard_data(days)
        return {
            "daily_stats": data["daily_stats"],
            "charts": data["charts"]
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))
