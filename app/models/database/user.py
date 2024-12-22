from sqlalchemy import Column, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.user import UserRole, UserStatus, UserSkill

class DBUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    skills = Column(String)  # Stored as comma-separated values
    monday_user_id = Column(String, unique=True)
    slack_user_id = Column(String, unique=True)
    team_id = Column(String, ForeignKey("teams.id"))
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    team = relationship("DBTeam", back_populates="members")
    assigned_tasks = relationship("DBTask", back_populates="assignee")
    created_tasks = relationship("DBTask", back_populates="creator")
    notifications = relationship("DBNotification", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("DBToken", back_populates="user", cascade="all, delete-orphan") 