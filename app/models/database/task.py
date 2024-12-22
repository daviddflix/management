from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from app.core.database import Base
from app.models.task import TaskStatus, TaskPriority, TaskType

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.BACKLOG)
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
    parent_task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
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
    subtasks = relationship("Task", backref=backref("parent", remote_side=[id]))
    board = relationship("Board", back_populates="tasks")