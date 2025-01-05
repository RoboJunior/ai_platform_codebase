from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.schemas.user import Token
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.db import models 
from app.services.auth_service import verify_password, create_access_token

auth_router = APIRouter()

@auth_router.post("/login", response_model=Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_database_session)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = create_access_token(data={"user_id": user.id})
    
    return {"access_token": access_token, "token_type":"bearer"}
