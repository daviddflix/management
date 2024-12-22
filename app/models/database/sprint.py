from sqlalchemy import Column, String, DateTime, Enum as SQLAlchemyEnum, Integer, ForeignKey, Float, JSON, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.sprint import SprintStatus

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    goal = Column(String, nullable=False)
    goals = Column(ARRAY(String), default=[])  # Additional goals list
    status = Column(SQLAlchemyEnum(SprintStatus), default=SprintStatus.PLANNING)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    velocity = Column(Float)
    monday_sprint_id = Column(String, nullable=True)
    monday_board_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields from the new model
    planned_tasks = Column(ARRAY(String), default=[])
    completed_tasks = Column(ARRAY(String), default=[])
    metrics = Column(JSON, default={})
    retrospective = Column(JSON, default={
        "what_went_well": [],
        "what_needs_improvement": [],
        "action_items": []
    })
    daily_standups = Column(JSON, default=[])
    blockers = Column(JSON, default=[])
    team_members = Column(ARRAY(String), default=[])

    # Relationships
    team = relationship("Team", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")