from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth import create_access_token, get_current_user, verify_password
from database.db_setup import get_db
from sqlalchemy.orm import Session
from app.models.user import User
router = APIRouter(tags=["Auth"])

@router.post("/login")
async def login(from_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == from_data.username).first()
    if not user or not verify_password(from_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer",
    }