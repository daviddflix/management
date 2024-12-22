from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class MessageBase(BaseModel):
    """Base Pydantic model for messages."""
    content: str = Field(..., description="The content of the message")
    channel_id: str = Field(..., description="The ID of the channel this message belongs to")
    attachments: Optional[List[Dict[str, str]]] = Field(None, description="List of attachments")

class MessageCreate(MessageBase):
    """Pydantic model for creating a message."""
    parent_id: Optional[str] = Field(None, description="The ID of the parent message if this is a reply")

class MessageResponse(MessageBase):
    """Pydantic model for message responses."""
    id: str = Field(..., description="The unique identifier of the message")
    sender_id: str = Field(..., description="The ID of the user who sent the message")
    parent_id: Optional[str] = Field(None, description="The ID of the parent message if this is a reply")
    reactions: Dict[str, List[str]] = Field(default_factory=dict, description="Reactions to the message")
    created_at: datetime = Field(..., description="When the message was created")
    updated_at: datetime = Field(..., description="When the message was last updated")
    is_edited: bool = Field(default=False, description="Whether the message has been edited")

    class Config:
        from_attributes = True

class MessageThread(BaseModel):
    """Pydantic model for a message thread."""
    parent_message: MessageResponse = Field(..., description="The parent message")
    replies: List[MessageResponse] = Field(default_factory=list, description="Replies to the parent message")
