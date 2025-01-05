from temporalio import activity
from app.services.user_service import send_welcome_email
from app.core.config import get_settings

@activity.defn
async def send_mail_to_user(user_email: str):
    user_name = user_email.split("@")[0]
    send_welcome_email(user_email, user_name, get_settings().SENDER_EMAIL, get_settings().SENDER_PASSWORD)
    return f"user email received at activity : {user_email}"