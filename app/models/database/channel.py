from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base, TimestampMixin

class ChannelType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"

# Association table for channel members
channel_members = Table(
    'channel_members',
    Base.metadata,
    Column('channel_id', String, ForeignKey('channels.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('is_admin', Boolean, default=False),
    Column('joined_at', DateTime(timezone=True), default=datetime.utcnow)
)

class DBChannel(Base, TimestampMixin):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    channel_type = Column(String, nullable=False, default=ChannelType.PUBLIC.value)
    created_by_id = Column(String, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    team_id = Column(String, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    is_archived = Column(Boolean, default=False)
    slack_channel_id = Column(String, unique=True)

    # Relationships
    created_by = relationship("DBUser", foreign_keys=[created_by_id])
    team = relationship("DBTeam", back_populates="channels")
    members = relationship("DBUser", secondary=channel_members, back_populates="channels")
    messages = relationship("DBMessage", back_populates="channel", cascade="all, delete-orphan")
                    