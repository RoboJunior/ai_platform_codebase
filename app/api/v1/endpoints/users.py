import os
from fastapi import status, Depends, APIRouter, BackgroundTasks
from sqlalchemy import delete
from app.api.v1.schemas.user import UserCreate, UserResponse, UserDelete
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from app.db import models
from app.services.user_service import hash_password, start_email_workflow
from app.services.auth_service import get_current_user, create_url_safe_token, decode_url_safe_token
from fastapi import HTTPException
from app.core.config import get_settings
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
# Path where the template folder resides
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'services', 'mail', 'templates')

templates = Jinja2Templates(directory=template_dir)

user_router = APIRouter()

@user_router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user: UserCreate, background_task: BackgroundTasks, db: Session = Depends(get_database_session)):
    # Check wheather the user email exist in the database or not.
    user_exist = db.query(models.User).filter(models.User.email == user.email).first()
    if user_exist:
        raise HTTPException(status_code=400, detail="Email already exist")
    # Convert the password into hashpassword
    hashed_password = hash_password(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict(), updated_at=datetime.utcnow())
    token = create_url_safe_token({"email": user.email, "created_at": datetime.utcnow().timestamp()})
    verification_link = f"http://{get_settings().DOMAIN}/v1/users/verify/{token}"
    # Render Jinja2 email template
    html_content = templates.TemplateResponse(
        "verification_mail.html",
        {"request": None, "verification_link": verification_link}
    ).body.decode("utf-8")  # Convert from bytes to string

    # Once all the details are satisfied then insert the database into database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Temporlio workflow to send verification mail to the user
    background_task.add_task(start_email_workflow, user.email, "Verify your Email", html_content)
    return UserResponse(email=user.email, name=user.name, created_at=datetime.utcnow(), message="Please check your email for the verification link.")

@user_router.delete('/delete_user', status_code=status.HTTP_200_OK, response_model=UserDelete)
async def delete_user(db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the current user 
    user = db.query(models.User).filter(models.User.email == current_user.email).first()

    # Check wheather its a valid user or not
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return user

@user_router.get('/verify/{token}')
async def verify_user_account(token: str, db: Session = Depends(get_database_session)):
    # Decode the token 
    token = decode_url_safe_token(token)
    # Extract the user email and the timestamp
    user_email = token.get("email")
    timestamp = token.get("created_at")
    # Convert time into utc format
    created_time = datetime.utcfromtimestamp(timestamp)
    # Check wheather the token is expired or not
    if datetime.utcnow() - created_time > timedelta(hours=24):
        raise HTTPException(status_code=403, detail="Token has expired")
    # Check wheather the token is valid or not
    if not user_email or not timestamp:
        raise HTTPException(status_code=403, detail="Invalid token!")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=403, detail="User not found!")
    if user.is_active:
        raise HTTPException(status_code=400, detail="User already verified!")
    # If valid user update the user details
    user.is_active = True
    user.updated_at = datetime.utcnow()
    user.verified_at = datetime.utcnow()
    # Add the updated user details to the database
    db.commit()
    db.refresh(user)

    return {"message": "User verified successfully", "email": user.email}
    

    

    
