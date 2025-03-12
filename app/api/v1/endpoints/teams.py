import os
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
# from app.services.user_service import generate_team_code
from app.services.auth_service import get_current_user, create_url_safe_token, decode_url_safe_token
from app.services.team_service import (
    fetch_all_teammates_from_database,
    change_user_role, create_new_team)
from app.services.mail.mail_service import start_email_workflow
from typing import List
from app.services.notification_service import start_app_notifications_workflow
from datetime import datetime
from app.core.config import get_settings
from fastapi.templating import Jinja2Templates
from datetime import timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
# Path where the template folder resides
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'services', 'mail', 'templates')

templates = Jinja2Templates(directory=template_dir)

team_router = APIRouter()

@team_router.post('/create_team', status_code=status.HTTP_201_CREATED, response_model=TeamCreate)
async def create_team(team_data: CreateTeam, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    new_team = create_new_team(current_user.id, team_data.name, db)
    return new_team

@team_router.post("/join_team_with_team_code", status_code=status.HTTP_201_CREATED, response_model=JoinTeamResponse)
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

@team_router.get("/join_team/{token}", status_code=status.HTTP_201_CREATED, response_model=JoinTeamResponse)
async def join_team(token: str, background_task: BackgroundTasks, db: Session = Depends(get_database_session)):
    # Decode the token url
    token = decode_url_safe_token(token)
    # Extract the user email, timestamp, team_code
    user_email = token.get("email")
    timestamp = token.get("created_at")
    team_code = token.get("team_code")
    # Convert time into utc format
    created_time = datetime.utcfromtimestamp(timestamp)
    # Check wheather the token is expired or not
    if datetime.utcnow() - created_time > timedelta(hours=24):
        raise HTTPException(status_code=403, detail="Token has expired")
    
    # Check if the user already exists
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Please register before joining team!")
    
    # Check if team exists
    team = db.query(models.Team).filter(models.Team.team_code == team_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if the user is already a part of the team 
    existing_membership = db.query(models.Membership).filter(
        models.Membership.user_id == user.id,
        models.Membership.team_id == team.id
    ).first()

    if existing_membership:
        raise HTTPException(status_code=400, detail="User is already part of this team")
    
    # Check wheather user got invited to the team
    is_invited = db.query(models.Invitations).filter(
        models.Invitations.team_id == team.id,
        models.Invitations.invited_user_email == user_email
        ).first()
    
    if not is_invited:
        raise HTTPException(status_code=403, detail="User have not invited to join the team")
    
    # Add user to the team with the role viewver
    membership = models.Membership(user_id=user.id, team_id=team.id, role=models.Role.VIEWER)
    db.add(membership)
    db.commit()
    background_task.add_task(start_app_notifications_workflow, [{"team_id": team.id}], f"New user {user_email} has joined the team!", db)
    return membership

@team_router.post("/invite/{team_id}", status_code=status.HTTP_201_CREATED)
def invite_team(team_id: int, invited_members: InviteToTeam, background_task: BackgroundTasks, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check if the team exists
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if the current user is the admin of the team
    is_admin = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id,
        models.Membership.role == models.Role.ADMIN,
    ).first()
    if not is_admin:
        raise HTTPException(status_code=403, detail="User doesn't have access to invite members to the team")
    
    team_details = db.query(models.Team).filter(models.Team.id == team_id).first()
    invited_users = []  # Store successfully invited users
    skipped_users = []  # Store users that weren't invited due to existing membership/invitation
    
    for email in invited_members.emails:
        try:
            invited_user = db.query(models.User).filter(models.User.email == email).first()

            if invited_user:
                # If the user is registered, check if they are already part of the team
                is_member = db.query(models.Membership).filter(
                    models.Membership.user_id == invited_user.id,
                    models.Membership.team_id == team_id
                ).first()
                if is_member:
                    skipped_users.append({"email": email, "reason": "Already a team member"})
                    continue  # Skip to next email instead of raising exception
            
            # Check if an invitation already exists for this email and team
            existing_invitation = db.query(models.Invitations).filter(
                models.Invitations.team_id == team_id,
                models.Invitations.invited_user_email == email
            ).first()

            if existing_invitation:
                skipped_users.append({"email": email, "reason": "Invitation already sent"})
                continue  # Skip to next email instead of raising exception

            # Add new invitation entry
            new_invitation = models.Invitations(team_id=team_id, invited_user_email=email)
            db.add(new_invitation)
            db.commit()
            db.refresh(new_invitation)

            # Get the username
            user_name = email.split("@")[0]

            # Generate a unique invite token for each user
            token = create_url_safe_token(
                {"email": email, "created_at": datetime.utcnow().timestamp(), 
                "team_code": team_details.team_code}
            )

            invitation_link = f"http://{get_settings().DOMAIN}/v1/teams/join_team/{token}"

            # Render Jinja2 email template
            html_content = templates.TemplateResponse(
                "invitation_mail.html",
                {"request": None, "username": user_name, 
                "team_name": team_details.name, "user_email": email,
                "invitation_link": invitation_link}
            ).body.decode("utf-8")

            # Send an invitation email in the background
            background_task.add_task(
                start_email_workflow, email, 
                f"You are invited To Join {team_details.name}!", html_content
            )

            invited_users.append(email)
            
        except Exception as e:
            # Log the error and continue with next email
            print(f"Error processing invitation for {email}: {str(e)}")
            skipped_users.append({"email": email, "reason": "Processing error"})
            continue

    return {
        "message": "Invitation process completed",
        "invited_users": invited_users,
        "skipped_users": skipped_users
    }

@team_router.get('/get_all_team_members/{team_id}', status_code=status.HTTP_200_OK, response_model=List[GetTeamMember])
def get_all_teammates(team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    teammates = fetch_all_teammates_from_database(current_user.id, team_id, db)
    return teammates

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
    membership = change_user_role(user_id, team_id, current_user.id, role_update, db)
    return membership