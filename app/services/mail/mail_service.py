from app.core.config import get_settings
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from pathlib import Path
from typing import List
from app.workers.temporal.workflows.user_email_workflow import UserEmailWorkflow
from typing import Union, Optional
import uuid
from temporalio.client import Client
from pydantic import EmailStr

BASE_DIR = Path(__file__).resolve().parent

# Intializing mail configuation
mail_configuation = ConnectionConfig(
    MAIL_USERNAME = get_settings().MAIL_USERNAME,
    MAIL_PASSWORD = get_settings().MAIL_PASSWORD,
    MAIL_FROM = get_settings().MAIL_FROM,
    MAIL_PORT = get_settings().MAIL_PORT,
    MAIL_SERVER = get_settings().MAIL_SERVER,
    MAIL_FROM_NAME = get_settings().MAIL_FROM_NAME,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER= Path(BASE_DIR, 'templates')
)

mail = FastMail(
    config=mail_configuation
)

def create_message(recipients: List[str], subject: str, body: str):
    message = MessageSchema(
        recipients=recipients,
        subject=subject,
        body=body,
        subtype=MessageType.html
    )
    return message

async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def start_email_workflow(email_addresses: Optional[Union[EmailStr, List[EmailStr]]], subject: str, html_content):
    if isinstance(email_addresses, list):
        email_addresses = ','.join(email_addresses)
    task_id = uuid.uuid4().hex
    client = await create_temporal_client()
    email_workflow = await client.execute_workflow(
        UserEmailWorkflow.run,
        id=task_id,
        task_queue="user-email-task-queue",
        args=[email_addresses, subject, html_content]
    )
    return email_workflow

async def dispatch_verification_email(email: str, subject: str, html_content: str):
    try:
        message = create_message([email], subject, html_content)
        await mail.send_message(message)
    except Exception as e:
        print("Failed to send email to user", e)