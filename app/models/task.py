from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class TaskType(str, Enum):
    FEATURE = "feature"
    BUG = "bug"
    TECH_DEBT = "tech_debt"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"

class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    DONE = "done"

class TaskMetrics(BaseModel):
    time_estimate: float = 0.0
    time_spent: float = 0.0
    review_time: float = 0.0
    bug_count: int = 0
    code_quality_score: float = 0.0
    test_coverage: float = 0.0

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    story_points: int = Field(ge=1, le=13)
    monday_task_id: Optional[str] = None
    labels: List[str] = []
    attachments: List[str] = []
    team_id: str

class TaskCreate(TaskBase):
    assignee_id: Optional[str] = None
    sprint_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    story_points: Optional[int] = None
    assignee_id: Optional[str] = None
    sprint_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    attachments: Optional[List[str]] = None

class TaskResponse(TaskBase):
    id: str
    status: TaskStatus = TaskStatus.BACKLOG
    created_at: datetime
    updated_at: datetime
    creator_id: str
    assignee_id: Optional[str] = None
    sprint_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = []
    blocked_by: List[str] = []
    blocks: List[str] = []
    metrics: TaskMetrics = TaskMetrics()
    comments: List[Dict] = []
    history: List[Dict] = []

    class Config:
        from_attributes = True