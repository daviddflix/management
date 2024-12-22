from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLAlchemyEnum, Integer, JSON, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

class TeamType(str, Enum):
    DEVELOPMENT = "development"
    PLATFORM = "platform"
    FEATURE = "feature"
    SUPPORT = "support"

class TeamStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FORMING = "forming"
    DISBANDED = "disbanded"

# SQLAlchemy Model
class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLAlchemyEnum(TeamType), nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(TeamStatus), default=TeamStatus.ACTIVE)
    monday_team_id = Column(String, nullable=True)
    slack_channel_id = Column(String, nullable=True)
    max_capacity = Column(Integer, default=100)
    working_hours = Column(JSON, default={
        "start": "09:00",
        "end": "17:00",
        "timezone": "UTC"
    })
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tech_lead_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    scrum_master_id = Column(String, ForeignKey("users.id"), nullable=True)
    member_ids = Column(ARRAY(String), default=[])
    current_sprint_id = Column(String, ForeignKey("sprints.id"), nullable=True)
    metrics = Column(JSON, default={})

    # Relationships
    tech_lead = relationship("User", foreign_keys=[tech_lead_id], back_populates="led_teams")
    product_owner = relationship("User", foreign_keys=[product_owner_id], back_populates="owned_teams")
    scrum_master = relationship("User", foreign_keys=[scrum_master_id], back_populates="mastered_teams")
    members = relationship("User", secondary="team_members", back_populates="teams")
    current_sprint = relationship("Sprint", back_populates="team")
    tasks = relationship("Task", back_populates="team")

# Pydantic Models (keep existing ones)
class TeamMetrics(BaseModel):
    velocity: float = 0.0
    capacity: int = 0  # Story points
    availability: float = 1.0  # Percentage
    bug_rate: float = 0.0
    code_review_time: float = 0.0  # Hours
    sprint_completion_rate: float = 0.0
    average_task_completion_time: float = 0.0  # Hours

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: TeamType
    description: Optional[str] = None
    monday_team_id: Optional[str] = None
    slack_channel_id: Optional[str] = None
    max_capacity: int = Field(default=100, description="Maximum story points per sprint")
    working_hours: dict = Field(default={
        "start": "09:00",
        "end": "17:00",
        "timezone": "UTC"
    })

class TeamCreate(TeamBase):
    tech_lead_id: str
    product_owner_id: Optional[str] = None
    scrum_master_id: Optional[str] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[TeamType] = None
    description: Optional[str] = None
    status: Optional[TeamStatus] = None
    max_capacity: Optional[int] = None
    working_hours: Optional[dict] = None
    tech_lead_id: Optional[str] = None
    product_owner_id: Optional[str] = None
    scrum_master_id: Optional[str] = None

class Team(TeamBase):
    id: str
    status: TeamStatus = TeamStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    tech_lead_id: str
    product_owner_id: Optional[str] = None
    scrum_master_id: Optional[str] = None
    member_ids: List[str] = []
    current_sprint_id: Optional[str] = None
    metrics: TeamMetrics = TeamMetrics()

    class Config:
        from_attributes = True