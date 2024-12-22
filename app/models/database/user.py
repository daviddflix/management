from sqlalchemy import Column, String, DateTime, Enum, Boolean, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.user import UserRole, UserStatus, UserSkill

class DBUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    skills = Column(ARRAY(String), default=[])
    monday_user_id = Column(String, unique=True, nullable=True)
    slack_user_id = Column(String, unique=True, nullable=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    current_sprint_id = Column(String, ForeignKey("sprints.id"), nullable=True)
    assigned_tasks = Column(ARRAY(String), default=[])
    completed_tasks = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    team = relationship("Team", back_populates="members")
    sprint = relationship("Sprint", back_populates="team_members")
    assigned_tasks_rel = relationship("Task", back_populates="assignee", foreign_keys="[Task.assignee_id]")
    created_tasks = relationship("Task", back_populates="creator", foreign_keys="[Task.creator_id]")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="sender", foreign_keys="[Message.sender_id]")
    created_channels = relationship("Channel", back_populates="created_by", foreign_keys="[Channel.created_by_id]")
    channels = relationship("Channel", secondary="channel_members", back_populates="members")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    owned_boards = relationship("Board", back_populates="owner", foreign_keys="[Board.owner_id]")
    member_boards = relationship("Board", secondary="board_members", back_populates="members")