from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.team import TeamType, TeamStatus

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(TeamType), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TeamStatus), default=TeamStatus.ACTIVE)
    monday_team_id = Column(String, unique=True, nullable=True)
    slack_channel_id = Column(String, unique=True, nullable=True)
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
    current_sprint = relationship("Sprint", foreign_keys=[current_sprint_id], back_populates="team")
    sprints = relationship("Sprint", back_populates="team", foreign_keys="Sprint.team_id")
    tasks = relationship("Task", back_populates="team")
    channels = relationship("Channel", back_populates="team", cascade="all, delete-orphan") 