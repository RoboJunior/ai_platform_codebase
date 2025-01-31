from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from typing import List

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    name: str
    email: EmailStr
    created_at: datetime
    message: str
    class Config:
        from_attributes = True

class UserDelete(BaseModel):
    name: str
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id : Optional[str] = None

class SendEmail(BaseModel):
    addresses: List[EmailStr]