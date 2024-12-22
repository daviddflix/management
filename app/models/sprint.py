from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class SprintStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"

class SprintMetrics(BaseModel):
    planned_points: int = 0
    completed_points: int = 0
    actual_velocity: float = 0.0
    burndown_data: List[Dict] = []  # Daily points remaining
    completion_rate: float = 0.0
    average_task_completion_time: float = 0.0
    bugs_found: int = 0
    bugs_fixed: int = 0
    code_review_time: float = 0.0  # Average hours
    team_availability: float = 0.0  # Percentage

class SprintBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    team_id: str
    start_date: datetime
    end_date: datetime
    goals: List[str]
    monday_sprint_id: Optional[str] = None

class SprintCreate(SprintBase):
    planned_tasks: List[str] = []  # List of task IDs
    planned_story_points: int

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[SprintStatus] = None
    goals: Optional[List[str]] = None
    planned_tasks: Optional[List[str]] = None

class SprintResponse(SprintBase):
    id: str
    status: SprintStatus = SprintStatus.PLANNING
    created_at: datetime
    updated_at: datetime
    planned_tasks: List[str] = []
    completed_tasks: List[str] = []
    metrics: SprintMetrics = SprintMetrics()
    retrospective: Dict = Field(default={
        "what_went_well": [],
        "what_needs_improvement": [],
        "action_items": []
    })
    daily_standups: List[Dict] = []
    blockers: List[Dict] = []
    team_members: List[str] = []  # List of user IDs

    class Config:
        from_attributes = True