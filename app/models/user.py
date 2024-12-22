from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

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
    is_active: bool = True

    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    hashed_password: str

    class Config:
        from_attributes = True

