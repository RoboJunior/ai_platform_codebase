from app.services.mail.mail_service import mail, create_message
from app.db import models
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.api.v1.schemas.team import UpdateUserRole
import secrets

async def send_team_invitation(email: str, subject: str, html_content: str):
    try:
        message = create_message([email], subject, html_content)
        await mail.send_message(message)
    except Exception as e:
        print("Failed to send email to user", e)

def generate_team_code() -> str:
    return secrets.token_hex(2).upper()

def fetch_all_teammates_from_database(user_id: int, team_id: int, db: Session):
    # Check wheather the team exist or not
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="team does not exist")
    
    # Check if the user is a member of the team
    is_member = db.query(models.Membership).filter(
        models.Membership.user_id == user_id,
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

def change_user_role(user_id: int, team_id: int, current_user_id: int, role_update: UpdateUserRole, db: Session):
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
        models.Membership.user_id == current_user_id,
        models.Membership.team_id == team_id,
        models.Membership.role == models.Role.ADMIN,
    ).first()
    if not is_admin:
        raise HTTPException(status_code=403, detail="You do not have permission to update roles in this team")
    
    # # Update the user's role
    membership.role = role_update.role
    db.commit()

    return membership

def create_new_team(user_id: int, team_name: str, db: Session):
    # Check if the user creating team is a valid user.
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Check if the user has already created a team
    existing_team = db.query(models.Membership).filter(models.Membership.user_id == user_id, models.Membership.role == models.Role.ADMIN).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="User can create only one team")
    # If both the condition passes allowing user to create a teams
    team_code = generate_team_code()
    new_team = models.Team(name=team_name, team_code=team_code)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    membership = models.Membership(user_id=user_id, team_id=new_team.id, role=models.Role.ADMIN)
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return new_team