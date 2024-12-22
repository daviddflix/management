from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class DBSprintMetrics(Base):
    __tablename__ = "sprint_metrics"

    id = Column(String, primary_key=True)
    sprint_id = Column(String, ForeignKey("sprints.id"), nullable=False)
    velocity = Column(Float, nullable=False, default=0.0)
    completion_rate = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=False, default=0.0)
    team_satisfaction = Column(Float, nullable=False, default=0.0)
    burndown_data = Column(JSON, default={})  # Store daily progress
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    sprint = relationship("DBSprint", back_populates="metrics")

class DBTeamMetrics(Base):
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
    team = relationship("DBTeam", back_populates="metrics")

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