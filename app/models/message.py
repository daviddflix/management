from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.user import UserResponse

class MessageReaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user: UserResponse
    reaction: str

class MessageAttachment(BaseModel):
    type: str = Field(..., description="Type of attachment (file, image, etc.)")
    url: str = Field(..., description="URL to the attachment")
    name: str = Field(..., description="Original filename")
    size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the attachment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")
    attachments: Optional[List[MessageAttachment]] = None

class MessageCreate(MessageBase):
    channel_id: str = Field(..., description="Channel ID where the message will be posted")
    parent_id: Optional[str] = Field(None, description="Parent message ID for replies")

class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=4000)
    attachments: Optional[List[MessageAttachment]] = None

class MessageReactionUpdate(BaseModel):
    reaction: str = Field(..., min_length=1, max_length=50, description="Emoji reaction to add/remove")

class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender_id: Optional[str]
    channel_id: str
    parent_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_edited: bool
    slack_message_ts: Optional[str] = None
    
    sender: Optional[UserResponse]
    reactions: List[MessageReaction] = []
    reply_count: int = Field(0, description="Number of replies to this message")
    read_by_count: int = Field(0, description="Number of users who have read this message")

class MessageThread(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent: MessageResponse
    replies: List[MessageResponse]
    participant_count: int = Field(0, description="Number of unique participants in the thread")

class MessageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    sender_id: Optional[str]
    channel_id: str
    created_at: datetime
    has_attachments: bool
    reaction_count: int = Field(0, description="Total number of reactions")
    reply_count: int = Field(0, description="Number of replies")
