from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.database.channel import ChannelType
from app.models.user import UserResponse
from app.models.team import TeamResponse

class ChannelMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user: UserResponse
    is_admin: bool = False

class ChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the channel")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the channel")
    channel_type: ChannelType = Field(default=ChannelType.PUBLIC, description="Type of the channel")

class ChannelCreate(ChannelBase):
    team_id: str = Field(..., description="Team ID this channel belongs to")
    member_ids: Optional[List[str]] = Field(default=None, description="Initial member IDs to add to the channel")

class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    channel_type: Optional[ChannelType] = None
    is_archived: Optional[bool] = None

class ChannelMemberUpdate(BaseModel):
    user_ids: List[str] = Field(..., description="List of user IDs to be added as members")
    is_admin: Optional[bool] = Field(False, description="Whether the added members should be admins")

class ChannelResponse(ChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    team_id: str
    created_by_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_archived: bool
    slack_channel_id: Optional[str] = None
    
    team: TeamResponse
    created_by: Optional[UserResponse]
    members: List[ChannelMember]
    message_count: int = Field(0, description="Number of messages in the channel")

class ChannelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    channel_type: ChannelType
    team_id: str
    member_count: int = Field(0, description="Number of members in the channel")
    unread_count: Optional[int] = Field(0, description="Number of unread messages for the current user")
    last_message_at: Optional[datetime] = None
