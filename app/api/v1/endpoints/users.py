import os
from fastapi import status, Depends, APIRouter, BackgroundTasks
from sqlalchemy import delete
from app.api.v1.schemas.user import UserCreate, UserResponse, UserDelete
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from app.db import models
from app.services.user_service import hash_password, create_new_otp, validate_otp
from app.services.auth_service import get_current_user, create_url_safe_token, decode_url_safe_token, verify_password
from app.services.mail.mail_service import start_email_workflow
from fastapi import HTTPException
from app.core.config import get_settings
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from pydantic import EmailStr

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

@user_router.post('/forget_password', status_code=status.HTTP_200_OK)
def forget_password(email: EmailStr, background_task: BackgroundTasks, db: Session = Depends(get_database_session)):
    # Get the current user
    user = db.query(models.User).filter(models.User.email == email).first()

    # Check wheather its a valid user or not
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create otp and add the otp to the database 
    created_otp = create_new_otp(db, user.id)

    html_content = templates.TemplateResponse(
        "forget_password_mail.html",
        {"request": None, "username": email.split("@")[0], 
        "user_email": email, "otp_code": created_otp}
    ).body.decode("utf-8")

    # Send the otp through mail to the user 
    background_task.add_task(start_email_workflow, email, "Password reset mail", html_content)

    ##TODO this will be changed to frontend url redirect page 
    return {"message": "Please verify your email for the otp"}

@user_router.post('/verify_otp', status_code=status.HTTP_200_OK)
def verify_otp(email: EmailStr, otp: str, db: Session = Depends(get_database_session)):
    user = db.query(models.User).filter(models.User.email == email).first()

    # Check wheather the user is valid user or not
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check wheather the otp is invalid or not 
    result = validate_otp(db, user.id, otp)

    # Return the error occured
    if "error" in result:
        raise HTTPException(status_code=404, detail=result['error'])

    ###TODO Here instead of this route it to a frontend page.
    return {"message": "OTP verified successfully!"}

@user_router.post('/reset_password', status_code=status.HTTP_200_OK)
def reset_password(email: EmailStr, otp: str, new_password: str, db: Session = Depends(get_database_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    # Check wheather the user is valid user or not
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Check wheather the otp is valid or not
    result = validate_otp(db, user.id, otp)
    # Return the error occured
    if "error" in result:
        raise HTTPException(status_code=404, detail=result['error'])
    # Check wheather the user is trying to set the old password as new password
    if verify_password(new_password, user.password):
        raise HTTPException(status_code=400, 
            detail="New password cannot be same as the old password")
    
    valid_otp = result['success']
    try:
        # Mark OTP as used BEFORE updating password
        valid_otp.used_at = datetime.utcnow()
        valid_otp.is_valid = False
        db.commit()
        # Update password
        user.password = hash_password(new_password)
        db.commit()
        db.refresh(user)
        ### TODO route this to frontend on successfully request 
        return {"message": "Password reset successful"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred"
        )

@user_router.get('/verify/{token}')
async def verify_user_account(token: str, background_task: BackgroundTasks, db: Session = Depends(get_database_session)):
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
    html_content = templates.TemplateResponse(
        "welcome_mail.html",
        {"request": None, "username": user_email.split("@")[0], "user_email": user_email}
    ).body.decode("utf-8")  # Convert from bytes to string
    background_task.add_task(start_email_workflow, user_email, "Welcome to the platform!", html_content)

    ##TODO this will be changed to frontend url redirect page 
    return {"message": "User verified successfully", "email": user.email}