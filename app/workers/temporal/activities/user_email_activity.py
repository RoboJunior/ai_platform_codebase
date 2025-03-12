from temporalio import activity
from app.services.mail.mail_service import dispatch_verification_email

@activity.defn
async def handle_email_workflow(email_address: str, subject: str, html_content: str):
    await dispatch_verification_email(email_address, subject, html_content)
    print(f"Email sent to user : {email_address} with subject: {subject}")
    return f"user email received at activity : {email_address}"