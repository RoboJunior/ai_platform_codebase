from sqlalchemy.orm import Session
from app.db import models
from fastapi import HTTPException

def get_user_role(user_id: int, team_id: int, db: Session):
    # Check if the user already exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if team exists
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if the user is a member of the team
    is_member = db.query(models.Membership).filter(
        models.Membership.user_id == user_id,
        models.Membership.team_id == team_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=400, detail="User is not a member of this team")
    
    # Get the role of the user 
    user_role = db.query(models.Membership).filter(
        models.Membership.user_id == user_id,
        models.Membership.team_id == team_id
    ).first()

    # Return the role of the user
    return user_role.role, team.name