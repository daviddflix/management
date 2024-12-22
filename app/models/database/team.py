from sqlalchemy import Column, String, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.team import TeamType

class DBTeam(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(TeamType), nullable=False)
    monday_team_id = Column(String, unique=True)
    slack_channel_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    active_sprint_id = Column(String, ForeignKey("sprints.id"))

    # Relationships
    members = relationship("DBUser", back_populates="team")
    sprints = relationship("DBSprint", back_populates="team")
    tasks = relationship("DBTask", back_populates="team") 