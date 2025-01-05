from fastapi import status, Depends, APIRouter, BackgroundTasks
from app.api.v1.schemas.user import UserCreate, UserResponse
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from app.db import models
from app.services.user_service import hash_password, start_email_workflow

user_router = APIRouter()

@user_router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user: UserCreate, background_task: BackgroundTasks, db: Session = Depends(get_database_session)):
    # Convert the password into hashpassword
    hashed_password = hash_password(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    start_email_workflow
    db.refresh(new_user)
    # await start_email_workflow(user.email)
    background_task.add_task(start_email_workflow, user.email)
    return new_user


