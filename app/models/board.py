from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from app.models.user import UserResponse
from app.models.task import TaskResponse
from app.models.team import TeamResponse

class BoardVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM = "team"

class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the board")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the board")
    visibility: BoardVisibility = Field(default=BoardVisibility.PRIVATE, description="Visibility level of the board")

class BoardCreate(BoardBase):
    team_id: Optional[str] = Field(None, description="Optional team ID to associate the board with")

class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: Optional[BoardVisibility] = None
    team_id: Optional[str] = None

class BoardMemberUpdate(BaseModel):
    user_ids: List[str] = Field(..., description="List of user IDs to be added as members")

class BoardResponse(BoardBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    team_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    owner: UserResponse
    members: List[UserResponse]
    tasks: List[TaskResponse]
    team: Optional[TeamResponse] = None

class BoardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    owner_id: str
    visibility: BoardVisibility
    task_count: int = Field(0, description="Number of tasks in the board")
    member_count: int = Field(0, description="Number of members in the board")
