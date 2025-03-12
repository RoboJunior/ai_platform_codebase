from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import timedelta
from datetime import datetime
from app.db import models
import string
import random

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

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
