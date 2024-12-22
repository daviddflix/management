from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import datetime
from app.models.team import Team, TeamCreate, TeamUpdate, TeamType
from app.services.monday_service import MondayService
from app.services.slack_service import SlackService
from app.core.config import settings
from app.core.security import get_current_user, check_permissions
from app.models.user import User
from app.core.deps import get_monday_service, get_slack_service
import re

router = APIRouter()

def validate_team_name(name: str) -> bool:
    """
    Validate team name for Slack channel compatibility
    - Only lowercase letters, numbers, hyphens, and underscores
    - Must start with a letter or number
    - Maximum length of 80 characters
    - No spaces or special characters
    """
    if not name or len(name) > 80:
        return False
    if not re.match(r"^[a-z0-9][a-z0-9-_]*$", name):
        return False
    return True

@router.get("/", response_model=List[Team])
async def get_teams(
    type: Optional[TeamType] = None,
    active_only: bool = True,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get all teams with optional filtering"""
    try:
        teams = await monday_service.get_teams(type=type, active_only=active_only)
        
        # Filter teams based on user permissions
        if not current_user.is_admin:
            teams = [
                team for team in teams
                if current_user.id in [member.id for member in team.members]
            ]
            
        return teams
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch teams: {str(e)}"
        )

@router.post("/", response_model=Team)
async def create_team(
    team: TeamCreate,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Create a new team (requires admin or tech lead role)"""
    try:
        # Validate team name
        if not validate_team_name(team.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid team name. Use only lowercase letters, numbers, hyphens, and underscores. Must start with a letter or number."
            )
            
        # Check if team name already exists
        existing_team = await monday_service.get_team_by_name(team.name)
        if existing_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team name already exists"
            )
            
        # Validate team size
        if len(team.member_ids) > settings.MAX_TEAM_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Team size cannot exceed {settings.MAX_TEAM_SIZE} members"
            )
            
        # Validate member existence
        for member_id in team.member_ids:
            member = await monday_service.get_user(member_id)
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {member_id} not found"
                )

        # Create team in Monday.com
        team_data = team.dict()
        team_data['created_by'] = current_user.id
        team_data['created_at'] = datetime.utcnow()
        created_team = await monday_service.create_team(team_data)
        
        # Create Slack channel
        try:
            if not team.slack_channel_id:
                channel_name = f"team-{team.name.lower().replace(' ', '-')}"
                channel = await slack_service.create_channel(channel_name)
                created_team.slack_channel_id = channel['id']
                await monday_service.update_team(
                    created_team.id,
                    {"slack_channel_id": channel['id']}
                )
                
                # Invite team members to the channel
                for member_id in team.member_ids:
                    user = await monday_service.get_user(member_id)
                    if user and user.slack_id:
                        await slack_service.invite_to_channel(
                            channel['id'],
                            user.slack_id
                        )
        except Exception as slack_error:
            # Log the error but don't fail the team creation
            print(f"Failed to create Slack channel: {str(slack_error)}")
        
        return created_team
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )

@router.get("/{team_id}", response_model=Team)
async def get_team(
    team_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific team by ID"""
    try:
        team = await monday_service.get_team(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this team"
            )
            
        return team
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch team: {str(e)}"
        )

@router.put("/{team_id}", response_model=Team)
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(get_current_user)
):
    """Update a team"""
    try:
        # Get existing team
        team = await monday_service.get_team(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id != team.created_by:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this team"
            )

        # Validate team name if being updated
        if team_update.name and team_update.name != team.name:
            if not validate_team_name(team_update.name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid team name. Use only lowercase letters, numbers, hyphens, and underscores. Must start with a letter or number."
                )
                
            # Check if new name already exists
            existing_team = await monday_service.get_team_by_name(team_update.name)
            if existing_team and existing_team.id != team_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Team name already exists"
                )

        # Validate team size if members are being updated
        if team_update.member_ids and len(team_update.member_ids) > settings.MAX_TEAM_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Team size cannot exceed {settings.MAX_TEAM_SIZE} members"
            )

        updated_team = await monday_service.update_team(
            team_id,
            team_update.dict(exclude_unset=True)
        )
        
        # Update Slack channel if name changed
        if team_update.name and team.slack_channel_id:
            try:
                new_channel_name = f"team-{team_update.name.lower().replace(' ', '-')}"
                await slack_service.rename_channel(
                    team.slack_channel_id,
                    new_channel_name
                )
            except Exception as slack_error:
                # Log the error but don't fail the team update
                print(f"Failed to rename Slack channel: {str(slack_error)}")
        
        return updated_team
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team: {str(e)}"
        )

@router.get("/{team_id}/members", response_model=List[str])
async def get_team_members(
    team_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a team"""
    try:
        team = await monday_service.get_team(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view team members"
            )
            
        members = await monday_service.get_team_members(team_id)
        return members
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch team members: {str(e)}"
        )

@router.post("/{team_id}/members/{user_id}")
async def add_team_member(
    team_id: str,
    user_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a team"""
    try:
        # Get team and validate existence
        team = await monday_service.get_team(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id != team.created_by:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add members to this team"
            )
            
        # Check if user exists
        user = await monday_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Check team size limit
        current_members = await monday_service.get_team_members(team_id)
        if len(current_members) >= settings.MAX_TEAM_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Team size cannot exceed {settings.MAX_TEAM_SIZE} members"
            )
            
        # Add member to team
        await monday_service.add_team_member(team_id, user_id)
        
        # Add member to Slack channel if exists
        if team.slack_channel_id and user.slack_id:
            try:
                await slack_service.invite_to_channel(
                    team.slack_channel_id,
                    user.slack_id
                )
            except Exception as slack_error:
                # Log the error but don't fail the member addition
                print(f"Failed to add member to Slack channel: {str(slack_error)}")
        
        return {"message": "Member added successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team member: {str(e)}"
        )

@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a team"""
    try:
        # Get team and validate existence
        team = await monday_service.get_team(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id != team.created_by:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove members from this team"
            )
            
        # Check if user exists and is a member
        user = await monday_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        members = await monday_service.get_team_members(team_id)
        if user_id not in [m.id for m in members]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a member of this team"
            )
            
        # Remove member from team
        await monday_service.remove_team_member(team_id, user_id)
        
        # Remove member from Slack channel if exists
        if team.slack_channel_id and user.slack_id:
            try:
                await slack_service.remove_from_channel(
                    team.slack_channel_id,
                    user.slack_id
                )
            except Exception as slack_error:
                # Log the error but don't fail the member removal
                print(f"Failed to remove member from Slack channel: {str(slack_error)}")
        
        return {"message": "Member removed successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}"
        ) 