from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class ActivityType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    TASK_ADDED = "task_added"
    TASK_REMOVED = "task_removed"
    STATUS_CHANGED = "status_changed"
    VISIBILITY_CHANGED = "visibility_changed"

class ActivityBase(BaseModel):
    board_id: int = Field(..., description="ID of the board this activity belongs to")
    user_id: int = Field(..., description="ID of the user who performed the action")
    action: ActivityType = Field(..., description="Type of action performed")
    details: str = Field(..., description="Additional details about the activity")

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    details: Optional[str] = None

class ActivityResponse(ActivityBase):
    model_config = {"from_attributes": True}
    
    id: int
    created_at: datetime
    board_name: str
    user_name: str
