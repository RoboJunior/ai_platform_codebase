from app.db.session import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, DateTime
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql import func
import enum
from datetime import datetime

# Enum for user roles
class Role(str, enum.Enum):
    ADMIN = "admin"
    VIEWER = "viewer"
    EDITOR = "editor"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String(150))
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.utcnow)
    created_at = Column(TIMESTAMP, server_default=func.now())
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notifications", back_populates="user", cascade="all, delete-orphan")
    otps = relationship("PasswordResetOTP", back_populates="user")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    team_code = Column(String, unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    memberships = relationship("Membership", back_populates="team", cascade="all, delete-orphan")
    invitations = relationship("Invitations", back_populates="team", cascade="all, delete-orphan")
    notifications = relationship("Notifications", back_populates="team", cascade="all, delete-orphan")

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    role = Column(Enum(Role), default=Role.VIEWER, nullable=False)

    user = relationship("User", back_populates="memberships")
    team = relationship("Team", back_populates="memberships")

class Invitations(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    invited_user_email = Column(String, nullable=False)

    team = relationship("Team", back_populates="invitations")

class Notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    message = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="notifications")
    team = relationship("Team", back_populates="notifications")

class PasswordResetOTP(Base):
    __tablename__ = "password_reset_opts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hashed_otp = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=True)
    attempts = Column(Integer, default=0)
    max_attempts = 5

    user = relationship("User", back_populates="otps")