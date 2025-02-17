from passlib.context import CryptContext
from temporalio.client import Client
from app.core.config import get_settings
from app.workers.temporal.workflows.user_email_workflow import UserEmailWorkflow
import uuid
from typing import List, Union, Optional
from pydantic import EmailStr
from app.services.mail.mail_service import mail, create_message
from sqlalchemy.orm import Session
from datetime import timedelta
from datetime import datetime
from app.db import models
import string
import random

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

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))

def create_new_otp(db: Session, user_id: int, expiry_minutes: int = 10):
    # Invalidate all existing OTPs
    db.query(models.PasswordResetOTP).filter(
        models.PasswordResetOTP.user_id == user_id,
        models.PasswordResetOTP.is_valid == True
    ).update({
        "is_valid": False
    })

    # Genearte 6 digit random otp
    otp = generate_otp()

    # Create new OTP record
    new_otp = models.PasswordResetOTP(
        user_id=user_id,
        hashed_otp=pwd_context.hash(str(otp)),
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes)
    )

    # Add the otp to the database
    db.add(new_otp)
    db.commit()
    return otp

def validate_otp(db: Session, user_id: int, otp: str):
    valid_otp = db.query(models.PasswordResetOTP).filter(
        models.PasswordResetOTP.user_id == user_id,
        models.PasswordResetOTP.is_valid == True,
        models.PasswordResetOTP.expires_at > datetime.utcnow(),
        models.PasswordResetOTP.used_at.is_(None)
    ).first()

    if not valid_otp:
        return {"error": "Invalid or expired OTP"}

    if valid_otp.attempts >= valid_otp.max_attempts:
        return {"error": "Too many failed attempts, please request a new OTP"}

    if not pwd_context.verify(otp, valid_otp.hashed_otp):
        valid_otp.attempts += 1
        db.commit()
        return {"error": "Invalid OTP"}

    # Reset attempts if OTP is correct
    valid_otp.attempts = 0
    db.commit()
    
    return {"success": valid_otp}
