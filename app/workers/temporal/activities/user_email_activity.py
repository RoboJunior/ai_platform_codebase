from temporalio import activity
from app.services.user_service import dispatch_verification_email
from app.core.config import get_settings

@activity.defn
async def handle_email_workflow(email_address: str, subject: str, html_content: str):
    await dispatch_verification_email(email_address, subject, html_content)
    return f"user email received at activity : {email_address}"