from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.core.database import Base

class MetricType(str, Enum):
    VELOCITY = "velocity"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    PRODUCTIVITY = "productivity"
    TEAM_HEALTH = "team_health"

# SQLAlchemy Models
class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    sprint_id = Column(String, ForeignKey("sprints.id"), nullable=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    quality = Column(JSON, default={})
    performance = Column(JSON, default={})
    productivity = Column(JSON, default={})
    team_health = Column(JSON, default={})
    custom_metrics = Column(JSON, default={})

    # Relationships
    team = relationship("Team", back_populates="metrics_snapshots")
    sprint = relationship("Sprint", back_populates="metrics_snapshots")

class MetricsThreshold(Base):
    __tablename__ = "metrics_thresholds"

    id = Column(String, primary_key=True)
    metric_name = Column(String, nullable=False)
    warning_threshold = Column(Float, nullable=False)
    critical_threshold = Column(Float, nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    notification_channels = Column(JSON, default=["slack"])

    # Relationships
    team = relationship("Team", back_populates="metrics_thresholds")

class MetricsAlert(Base):
    __tablename__ = "metrics_alerts"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String, nullable=False)
    current_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # warning/critical
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="open")  # open/acknowledged/resolved
    acknowledged_by = Column(String, ForeignKey("users.id"), nullable=True)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)
    resolution_comment = Column(String, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="metrics_alerts")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

# Pydantic Models (keep existing ones)
class QualityMetrics(BaseModel):
    code_coverage: float = 0.0
    bug_density: float = 0.0
    technical_debt_ratio: float = 0.0
    code_smells: int = 0
    duplications: float = 0.0  # Percentage
    maintainability_index: float = 0.0
    security_issues: int = 0
    test_success_rate: float = 0.0

class PerformanceMetrics(BaseModel):
    sprint_completion_rate: float = 0.0
    average_cycle_time: float = 0.0  # Days
    average_lead_time: float = 0.0  # Days
    blocked_time_ratio: float = 0.0
    review_time: float = 0.0  # Hours
    deployment_frequency: float = 0.0  # Per week
    deployment_success_rate: float = 0.0

class ProductivityMetrics(BaseModel):
    velocity_trend: List[float] = []
    story_points_completed: int = 0
    tasks_completed: int = 0
    commits_per_day: float = 0.0
    pr_merge_rate: float = 0.0
    code_review_participation: float = 0.0

class TeamHealthMetrics(BaseModel):
    team_happiness: float = 0.0
    team_stress: float = 0.0
    overtime_hours: float = 0.0
    meeting_time_ratio: float = 0.0
    collaboration_index: float = 0.0
    knowledge_sharing_score: float = 0.0
