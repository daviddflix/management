from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class NotificationBase(BaseModel):
    """Base Pydantic model for notifications."""
    title: str = Field(..., max_length=255, description="Title of the notification")
    message: str = Field(..., max_length=1000, description="Content of the notification")
    type: str = Field(..., description="Type of notification (info, warning, error)")

class NotificationCreate(NotificationBase):
    """Pydantic model for creating a notification."""
    user_id: str = Field(..., description="ID of the user to notify")

class NotificationResponse(NotificationBase):
    """Pydantic model for notification responses."""
    id: str = Field(..., description="The unique identifier of the notification")
    user_id: str = Field(..., description="ID of the user who received the notification")
    is_read: bool = Field(default=False, description="Whether the notification has been read")
    created_at: datetime = Field(..., description="When the notification was created")
    updated_at: datetime = Field(..., description="When the notification was last updated")

    model_config = ConfigDict(from_attributes=True)
