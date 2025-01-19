from fastapi import status, HTTPException, Depends, APIRouter, BackgroundTasks
from app.api.v1.schemas.team import (
    CreateTeam, TeamCreate, 
    JoinTeam, JoinTeamResponse, 
    InviteToTeam, GetTeamMember, 
    RemoveTeamMember, LeaveFromTeam, 
    UpdateUserRole, UpdateUserRoleResponse)
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from app.db import models
from app.services.user_service import generate_team_code
from app.services.auth_service import get_current_user
from app.services.team_service import start_invitation_email_workflow
from typing import List
from app.services.notification_service import start_app_notifications_workflow

team_router = APIRouter()

@team_router.post('/create_team', status_code=status.HTTP_201_CREATED, response_model=TeamCreate)
async def create_team(team_data: CreateTeam, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check if the user creating team is a valid user.
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Check if the user has already created a team
    existing_team = db.query(models.Membership).filter(models.Membership.user_id == current_user.id, models.Membership.role == models.Role.ADMIN).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="User can create only one team")
    # If both the condition passes allowing user to create a teams
    team_code = generate_team_code()
    new_team = models.Team(name=team_data.name, team_code=team_code)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    membership = models.Membership(user_id=current_user.id, team_id=new_team.id, role=models.Role.ADMIN)
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return new_team

@team_router.post("/join_team", status_code=status.HTTP_201_CREATED, response_model=JoinTeamResponse)
async def join_team(team_data: JoinTeam, background_task: BackgroundTasks, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check if the user already exists
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if team exists
    team = db.query(models.Team).filter(models.Team.team_code == team_data.team_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if the user is already a part of the team 
    existing_membership = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team.id
    ).first()

    if existing_membership:
        raise HTTPException(status_code=400, detail="User is already part of this team")
    
    # Check wheather user got invited to the team
    is_invited = db.query(models.Invitations).filter(
        models.Invitations.team_id == team.id,
        models.Invitations.invited_user_email == current_user.email
        ).first()
    
    if not is_invited:
        raise HTTPException(status_code=403, detail="User have not invited to join the team")
    
    # Add user to the team with the role viewver
    membership = models.Membership(user_id=current_user.id, team_id=team.id, role=models.Role.VIEWER)
    db.add(membership)
    db.commit()
    background_task.add_task(start_app_notifications_workflow, [{"team_id": team.id}], f"New user {current_user.email} has joined the team!", db)
    return membership

@team_router.post("/invite/{team_id}", status_code=status.HTTP_201_CREATED)
def invite_team(team_id: int, invited_member: InviteToTeam, background_task: BackgroundTasks, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check wheather the team exists or not
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Getting all the team details
    team_details = db.query(models.Team).filter(models.Team.id == team_id).first()
    
    # Check wheather the current user is the admin of the team
    is_admin = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id,
        models.Membership.role == models.Role.ADMIN,
    ).first()
    if not is_admin:
        raise HTTPException(status_code=403, detail="User doesnt have access to invite members to the team")

    # Check wheather the user is already part of the system or not
    invited_user = db.query(models.User).filter(models.User.email == invited_member.email).first()
    if invited_user:
        # If the user is registerd check if they are already part of the team
        is_member = db.query(models.Membership).filter(
            models.Membership.user_id == invited_user.id,
            models.Membership.team_id == team_id
        ).first()
        if is_member:
            raise HTTPException(status_code=400, detail="User already a member of the team")
    else:
        print(team.email, team_details.name, team_details.team_code)
        new_invitation = models.Invitations(team_id=team_id, invited_user_email=invited_member.email)
        db.add(new_invitation)
        db.commit()
        db.refresh(new_invitation)
        background_task.add_task(start_invitation_email_workflow, team.email, team_details.name, team_details.team_code)
        return new_invitation
    
    new_invitation = models.Invitations(team_id=team_id, invited_user_email=invited_member.email)
    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    background_task.add_task(start_invitation_email_workflow, invited_member.email, team_details.name, team_details.team_code)
    return new_invitation

@team_router.get('/get_all_team_members/{team_id}', status_code=status.HTTP_200_OK, response_model=List[GetTeamMember])
def get_all_teammates(team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check wheather the team exist or not
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="team does not exist")
    
    # Check if the user is a member of the team
    is_member = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id
    ).first()
    print(is_member)
    if not is_member:
        raise HTTPException(status_code=403, detail="User doesnt have access to view team members")
    
    # Get all the team members 
    team_members = db.query(models.Membership, models.User).join(
        models.User, models.User.id == models.Membership.user_id
    ).filter(models.Membership.team_id == team_id).all()

    members_info = [
        {
            "id": member.User.id,
            "email": member.User.email,
            "role": member.Membership.role,
            "created_time": member.User.created_at
        }
        for member in team_members
    ]
    return members_info

@team_router.delete('/remove_user/{user_id}/{team_id}', response_model=RemoveTeamMember)
def remove_user_from_the_team(user_id: int, team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check wheather the team exist or not
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team doesnt exist")
    
    # Check wheather the user exist or not
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User doesnt exist")
    
    # Check if the user is a member of the team
    is_member = db.query(models.Membership).filter(
        models.Membership.user_id == user_id,
        models.Membership.team_id == team_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=400, detail="User is not a member of this team")
    
    # Check wheather the current user is the admin of the team
    is_admin = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id,
        models.Membership.role == models.Role.ADMIN,
    ).first()
    if not is_admin:
        raise HTTPException(status_code=403, detail="User doesnt have access to remove team member")
    
    is_invited = db.query(models.Invitations).filter(
        models.Invitations.team_id == team_id,
        models.Invitations.invited_user_email == current_user.email
    ).first()
    
    # Delete the invitation of the user preventing the user from joining the team again without any admin permission
    db.delete(is_invited)
    db.commit()
    
    # Commit the deleted data into the database
    db.delete(is_member)
    db.commit()
    return user

@team_router.delete('/leave_team/{team_id}', status_code=status.HTTP_200_OK, response_model=LeaveFromTeam)
async def leave_from_team(team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check wheather the team exists or not 
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

     # Check if the user is a member of the team
    is_member = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=400, detail="You are not the member of the team")
    
    is_invited = db.query(models.Invitations).filter(
        models.Invitations.team_id == team_id,
        models.Invitations.invited_user_email == current_user.email
    ).first()
    
    # Delete the invitation of the user preventing the user from joining the team again without any admin permission
    db.delete(is_invited)
    db.commit()

    # Commit the deleted data to the database
    db.delete(is_member)
    db.commit()

    return current_user

@team_router.put('/update_user_role/{user_id}/{team_id}', response_model=UpdateUserRoleResponse)
def update_user_role(user_id: int, team_id: int, role_update: UpdateUserRole, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check if the team exists
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team does not exist")

    # Check if the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    # Check if the user is a member of the team
    membership = db.query(models.Membership).filter(
        models.Membership.user_id == user_id,
        models.Membership.team_id == team_id
    ).first()
    if not membership:
        raise HTTPException(status_code=400, detail="User is not a member of this team")
    
    # Check if the current user is an admin of the team
    is_admin = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id,
        models.Membership.role == models.Role.ADMIN,
    ).first()
    if not is_admin:
        raise HTTPException(status_code=403, detail="You do not have permission to update roles in this team")
    
    # # Update the user's role
    membership.role = role_update.role
    db.commit()

    return membership