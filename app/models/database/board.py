from sqlalchemy import Column, String, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin
from app.models.board import BoardVisibility

# Association table for board members
board_members = Table(
    'board_members',
    Base.metadata,
    Column('board_id', String, ForeignKey('boards.id', ondelete='CASCADE')),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE'))
)

class Board(Base, TimestampMixin):
    __tablename__ = 'boards'

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    owner_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    visibility = Column(SQLEnum(BoardVisibility), default=BoardVisibility.PRIVATE)

    # Relationships
    owner = relationship("DBUser", back_populates="owned_boards", foreign_keys=[owner_id])
    members = relationship("DBUser", secondary=board_members, back_populates="member_boards")
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan")
    team = relationship("Team", back_populates="boards")
    activities = relationship("Activity", back_populates="board", cascade="all, delete-orphan")
