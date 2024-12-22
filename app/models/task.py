from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLAlchemyEnum, Integer, Float, JSON, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

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

# SQLAlchemy Model
class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    type = Column(SQLAlchemyEnum(TaskType), nullable=False)
    priority = Column(SQLAlchemyEnum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.BACKLOG)
    story_points = Column(Integer, nullable=False)
    monday_task_id = Column(String, nullable=True)
    labels = Column(ARRAY(String), default=[])
    attachments = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    sprint_id = Column(String, ForeignKey("sprints.id"), nullable=True)
    dependencies = Column(ARRAY(String), default=[])
    blocked_by = Column(ARRAY(String), default=[])
    blocks = Column(ARRAY(String), default=[])
    metrics = Column(JSON, default={})
    comments = Column(JSON, default=[])
    history = Column(JSON, default=[])

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    team = relationship("Team", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")

class TaskMetrics(BaseModel):
    time_estimate: float = 0.0  # Hours
    time_spent: float = 0.0  # Hours
    review_time: float = 0.0  # Hours
    bug_count: int = 0
    code_quality_score: float = 0.0
    test_coverage: float = 0.0

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    story_points: int = Field(ge=1, le=13)  # Fibonacci: 1,2,3,5,8,13
    monday_task_id: Optional[str] = None
    labels: List[str] = []
    attachments: List[str] = []

class TaskCreate(TaskBase):
    assignee_id: Optional[str] = None
    sprint_id: Optional[str] = None
    dependencies: List[str] = []  # List of task IDs
    team_id: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    story_points: Optional[int] = None
    assignee_id: Optional[str] = None
    sprint_id: Optional[str] = None
    dependencies: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    attachments: Optional[List[str]] = None

class Task(TaskBase):
    id: str
    status: TaskStatus = TaskStatus.BACKLOG
    created_at: datetime
    updated_at: datetime
    creator_id: str
    assignee_id: Optional[str] = None
    team_id: str
    sprint_id: Optional[str] = None
    dependencies: List[str] = []
    blocked_by: List[str] = []
    blocks: List[str] = []
    metrics: TaskMetrics = TaskMetrics()
    comments: List[Dict] = []
    history: List[Dict] = []

    class Config:
        from_attributes = True