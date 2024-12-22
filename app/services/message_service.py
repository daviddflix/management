from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import uuid

from app.models.message import MessageCreate, MessageResponse, MessageThread
from app.models.database.message import DBMessage
from app.models.database.channel import DBChannel
from app.models.database.user import DBUser

class MessageService:
    def __init__(self, db: Session):
        self.db = db

    async def create_message(self, message: MessageCreate, sender_id: str) -> MessageResponse:
        """Create a new message."""
        # Verify channel exists
        channel = self.db.query(DBChannel).filter(DBChannel.id == message.channel_id).first()
        if not channel:
            raise Exception("Channel not found")

        db_message = DBMessage(
            id=str(uuid.uuid4()),
            content=message.content,
            channel_id=message.channel_id,
            sender_id=sender_id,
            parent_id=message.parent_id,
            attachments=message.attachments,
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return self._to_response(db_message)

    async def get_channel_messages(self, channel_id: str) -> List[MessageResponse]:
        """Get all messages in a channel."""
        messages = (
            self.db.query(DBMessage)
            .filter(DBMessage.channel_id == channel_id)
            .filter(DBMessage.parent_id.is_(None))  # Only get top-level messages
            .order_by(desc(DBMessage.created_at))
            .all()
        )
        return [self._to_response(msg) for msg in messages]

    async def get_message_thread(self, message_id: str) -> MessageThread:
        """Get a message thread (parent message and all replies)."""
        parent_message = (
            self.db.query(DBMessage)
            .filter(DBMessage.id == message_id)
            .first()
        )
        if not parent_message:
            raise Exception("Message not found")

        replies = (
            self.db.query(DBMessage)
            .filter(DBMessage.parent_id == message_id)
            .order_by(DBMessage.created_at)
            .all()
        )

        return MessageThread(
            parent_message=self._to_response(parent_message),
            replies=[self._to_response(msg) for msg in replies]
        )

    async def add_reaction(self, message_id: str, user_id: str, reaction: str) -> None:
        """Add a reaction to a message."""
        message = self.db.query(DBMessage).filter(DBMessage.id == message_id).first()
        if not message:
            raise Exception("Message not found")

        if not message.reactions:
            message.reactions = {}
        
        if reaction not in message.reactions:
            message.reactions[reaction] = []
            
        if user_id not in message.reactions[reaction]:
            message.reactions[reaction].append(user_id)
            self.db.commit()

    async def remove_reaction(self, message_id: str, user_id: str, reaction: str) -> None:
        """Remove a reaction from a message."""
        message = self.db.query(DBMessage).filter(DBMessage.id == message_id).first()
        if not message:
            raise Exception("Message not found")

        if not message.reactions or reaction not in message.reactions:
            return

        if user_id in message.reactions[reaction]:
            message.reactions[reaction].remove(user_id)
            if not message.reactions[reaction]:
                del message.reactions[reaction]
            self.db.commit()

    def _to_response(self, message: DBMessage) -> MessageResponse:
        """Convert a database message to a response model."""
        return MessageResponse(
            id=message.id,
            content=message.content,
            channel_id=message.channel_id,
            sender_id=message.sender_id,
            parent_id=message.parent_id,
            attachments=message.attachments,
            reactions=message.reactions or {},
            created_at=message.created_at,
            updated_at=message.updated_at,
            is_edited=message.is_edited
        )

