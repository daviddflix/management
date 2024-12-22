from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base, TimestampMixin

# Association table for message reactions
message_reactions = Table(
    'message_reactions',
    Base.metadata,
    Column('message_id', String, ForeignKey('messages.id', ondelete='CASCADE')),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
    Column('reaction', String(50))
)

# Table for tracking message read status
message_reads = Table(
    'message_reads',
    Base.metadata,
    Column('message_id', String, ForeignKey('messages.id', ondelete='CASCADE')),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
    Column('read_at', DateTime, default=datetime.utcnow)
)

class DBMessage(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    content = Column(String(4000), nullable=False)
    sender_id = Column(String, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    channel_id = Column(String, ForeignKey('channels.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(String, ForeignKey('messages.id', ondelete='CASCADE'), nullable=True)
    is_edited = Column(Boolean, default=False)
    attachments = Column(JSON)  # Store attachment metadata
    reactions = Column(JSON, default={})  # Dict[str, List[str]] - emoji: [user_ids]
    slack_message_ts = Column(String, unique=True)
    
    # Relationships
    sender = relationship("DBUser", back_populates="messages")
    channel = relationship("DBChannel", back_populates="messages")
    parent = relationship("DBMessage", remote_side=[id], backref="replies")
    read_by = relationship("DBUser", secondary=message_reads)
