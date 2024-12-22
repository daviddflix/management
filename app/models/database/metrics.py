from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class SprintMetrics(Base):
    __tablename__ = "sprint_metrics"

    id = Column(String, primary_key=True)
    sprint_id = Column(String, ForeignKey("sprints.id"))
    velocity = Column(JSON)
    burndown = Column(JSON)
    task_distribution = Column(JSON)
    member_contribution = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sprint = relationship("Sprint", back_populates="metrics")

class TeamMetrics(Base):
    __tablename__ = "team_metrics"

    id = Column(String, primary_key=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    average_velocity = Column(Float, nullable=False, default=0.0)
    average_quality_score = Column(Float, nullable=False, default=0.0)
    sprint_completion_rate = Column(Float, nullable=False, default=0.0)
    team_health_score = Column(Float, nullable=False, default=0.0)
    historical_data = Column(JSON, default={})  # Store historical performance
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    team = relationship("Team", back_populates="metrics")

class DBTaskMetrics(Base):
    __tablename__ = "task_metrics"

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    cycle_time = Column(Integer, nullable=False, default=0)  # Time from start to completion
    review_time = Column(Integer, nullable=False, default=0)  # Time spent in review
    rework_count = Column(Integer, nullable=False, default=0)  # Number of times returned for rework
    quality_score = Column(Float, nullable=False, default=0.0)
    complexity_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    task = relationship("DBTask", back_populates="metrics")