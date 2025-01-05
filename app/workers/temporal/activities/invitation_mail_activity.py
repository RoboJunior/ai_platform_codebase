from temporalio import activity
from app.services.team_service import send_team_invitation
from app.core.config import get_settings

@activity.defn
async def send_invitation_mail_to_user(user_email: str, team_name: str, team_code: str):
    user_name = user_email.split("@")[0]
    send_team_invitation(user_email, user_name, team_name, team_code, get_settings().SENDER_EMAIL, get_settings().SENDER_PASSWORD)
    return f"user email received at activity : {user_email}"
