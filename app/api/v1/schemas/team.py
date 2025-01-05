from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.models import Role

class CreateTeam(BaseModel):
    name: str

class TeamCreate(BaseModel):
    id: int
    name: str
    team_code: str
    created_at: datetime
    class Config:
        from_attributes = True

class JoinTeam(BaseModel):
    team_code: str

class JoinTeamResponse(BaseModel):
    id: int
    user_id: int
    team_id: int
    role: str

class InviteToTeam(BaseModel):
    email: EmailStr

class GetTeamMember(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_time: datetime

    class Config:
        from_attributes = True

class RemoveTeamMember(BaseModel):
    id: int
    email: EmailStr

class LeaveFromTeam(RemoveTeamMember):
    pass

class UpdateUserRole(BaseModel):
    role: Role

class UpdateUserRoleResponse(BaseModel):
    user_id: int
    team_id: int
    role: str