from passlib.context import CryptContext
from temporalio.client import Client
from app.core.config import get_settings
from app.workers.temporal.workflows.user_email_workflow import UserEmailWorkflow
import uuid
from typing import List, Union, Optional
from pydantic import EmailStr
from app.services.mail.mail_service import mail, create_message

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

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
