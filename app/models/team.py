from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

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

class TeamResponse(TeamBase):
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