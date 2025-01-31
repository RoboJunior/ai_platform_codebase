from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime
from app.core.config import get_settings
from temporalio.client import Client
import uuid
from app.workers.temporal.workflows.invitation_mail_workflow import InvitationEmailWorkflow
from typing import Optional, Union, List
from pydantic import EmailStr
from app.services.mail.mail_service import mail, create_message

async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def start_invitation_email_workflow(email_addresses: Optional[Union[EmailStr, List[EmailStr]]], subject: str, html_content):
    if isinstance(email_addresses, list):
        email_addresses = ','.join(email_addresses)
    task_id = uuid.uuid4().hex
    client = await create_temporal_client()
    invitation_email_workflow = await client.execute_workflow(
        InvitationEmailWorkflow.run,
        id=task_id,
        task_queue="invitation-email-task-queue",
        args=[email_addresses, subject, html_content]
    )
    return invitation_email_workflow

async def send_team_invitation(email: str, subject: str, html_content: str):
    try:
        message = create_message([email], subject, html_content)
        await mail.send_message(message)
    except Exception as e:
        print("Failed to send email to user", e)