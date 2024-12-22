from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLAlchemyEnum, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, Enum):
    DEVELOPER = "developer"
    TECH_LEAD = "tech_lead"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"

class UserSkill(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    MOBILE = "mobile"
    FULLSTACK = "fullstack"
    UI_UX = "ui_ux"
    QA = "qa"
    TEAM_LEAD = "team_lead"

# SQLAlchemy Model
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    status = Column(SQLAlchemyEnum(UserStatus), default=UserStatus.ACTIVE)
    skills = Column(ARRAY(String), default=[])
    monday_user_id = Column(String, nullable=True)
    slack_user_id = Column(String, nullable=True)
    team_id = Column(String, nullable=False)
    current_sprint_id = Column(String, nullable=True)
    assigned_tasks = Column(ARRAY(String), default=[])
    completed_tasks = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with notifications
    notifications = relationship("Notification", back_populates="user")

# Pydantic Models (API Schemas)
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: UserRole
    skills: List[UserSkill] = []
    monday_user_id: Optional[str] = None
    slack_user_id: Optional[str] = None
    team_id: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    skills: Optional[List[UserSkill]] = None
    status: Optional[UserStatus] = None

class UserResponse(UserBase):
    id: str
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    current_sprint_id: Optional[str] = None
    assigned_tasks: List[str] = []
    completed_tasks: List[str] = []

    class Config:
        from_attributes = True