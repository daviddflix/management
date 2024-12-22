from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.sprint import SprintStatus

class DBSprint(Base):
    __tablename__ = "sprints"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    status = Column(Enum(SprintStatus), default=SprintStatus.PLANNING)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    velocity = Column(Float)
    team_id = Column(String, ForeignKey("teams.id"))
    monday_board_id = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    team = relationship("DBTeam", back_populates="sprints")
    tasks = relationship("DBTask", back_populates="sprint") 