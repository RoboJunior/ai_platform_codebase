from temporalio import activity
from app.services.team_service import send_team_invitation
from app.core.config import get_settings

@activity.defn
async def send_invitation_mail_to_user(email_address: str, subject: str, html_content: str):
    await send_team_invitation(email_address, subject, html_content)
    return f"user email received at activity : {email_address}"
