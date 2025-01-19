from fastapi import status, Depends, APIRouter, BackgroundTasks
from sqlalchemy import delete
from app.api.v1.schemas.user import UserCreate, UserResponse
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from app.db import models
from app.services.user_service import hash_password, start_email_workflow
from app.services.auth_service import get_current_user
from fastapi import HTTPException

user_router = APIRouter()

@user_router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user: UserCreate, background_task: BackgroundTasks, db: Session = Depends(get_database_session)):
    # Convert the password into hashpassword
    hashed_password = hash_password(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # await start_email_workflow(user.email)
    background_task.add_task(start_email_workflow, user.email)
    return new_user

@user_router.delete('/delete_user', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def delete_user(db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the current user 
    user = db.query(models.User).filter(models.User.email == current_user.email).first()

    # Check wheather its a valid user or not
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return user

# @user_router.put('/update_user', status_code=status.HTTP_200_OK)
# async def 
