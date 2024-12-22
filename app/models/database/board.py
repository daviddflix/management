from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.database.task import Task
from app.core.database import Base

# Association table for board members
board_members = Table(
    'board_members',
    Base.metadata,
    Column('board_id', Integer, ForeignKey('boards.id', ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'))
)

class BoardVisibility(str):
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM = "team"

class Board(Base):
    __tablename__ = 'boards'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    visibility = Column(SQLEnum(BoardVisibility), default=BoardVisibility.PRIVATE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_boards", foreign_keys=[owner_id])
    members = relationship("User", secondary=board_members, back_populates="member_boards")
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan")
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    team = relationship("Team", back_populates="boards")
