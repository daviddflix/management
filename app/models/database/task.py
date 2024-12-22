from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.task import TaskStatus, TaskPriority

class DBTask(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    story_points = Column(Integer)
    assignee_id = Column(String, ForeignKey("users.id"))
    creator_id = Column(String, ForeignKey("users.id"))
    sprint_id = Column(String, ForeignKey("sprints.id"))
    team_id = Column(String, ForeignKey("teams.id"))
    monday_item_id = Column(String)
    parent_task_id = Column(String, ForeignKey("tasks.id"))
    dependencies = Column(ARRAY(String))  # Array of task IDs
    labels = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationships
    assignee = relationship("DBUser", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = relationship("DBUser", foreign_keys=[creator_id], back_populates="created_tasks")
    sprint = relationship("DBSprint", back_populates="tasks")
    team = relationship("DBTeam", back_populates="tasks")
    subtasks = relationship("DBTask", backref="parent_task") 