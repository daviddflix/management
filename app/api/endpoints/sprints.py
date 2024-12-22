from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import date, datetime, timedelta
import pytz
from app.models.sprint import Sprint, SprintCreate, SprintUpdate, SprintStatus
from app.services.monday_service import MondayService
from app.services.slack_service import SlackService
from app.core.config import settings
from app.core.security import get_current_user, check_permissions
from app.models.user import User
from app.core.deps import get_monday_service, get_openai_service, get_slack_service

router = APIRouter()

def validate_sprint_dates(start_date: date, end_date: date, team_id: str, monday_service: MondayService) -> None:
    """
    Validate sprint dates:
    - End date must be after start date
    - Sprint duration must be within limits
    - No overlapping sprints for the same team
    """
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
        
    duration = (end_date - start_date).days
    if duration < settings.MIN_SPRINT_DURATION or duration > settings.MAX_SPRINT_DURATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sprint duration must be between {settings.MIN_SPRINT_DURATION} and {settings.MAX_SPRINT_DURATION} days"
        )

async def check_sprint_overlap(team_id: str, start_date: date, end_date: date, monday_service: MondayService) -> None:
    """Check for overlapping sprints"""
    overlapping = await monday_service.get_overlapping_sprints(team_id, start_date, end_date)
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint dates overlap with existing sprint"
        )

@router.get("/", response_model=List[Sprint])
async def get_sprints(
    team_id: Optional[str] = None,
    status: Optional[SprintStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get all sprints with optional filtering"""
    try:
        # Convert dates to UTC
        if start_date:
            start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=pytz.UTC)
        if end_date:
            end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=pytz.UTC)
            
        # Validate date range
        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        sprints = await monday_service.get_sprints(
            team_id=team_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        # Filter sprints based on user permissions
        if not current_user.is_admin:
            sprints = [
                sprint for sprint in sprints
                if current_user.id in [m.id for m in sprint.team.members]
            ]
            
        return sprints
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sprints: {str(e)}"
        )

@router.post("/", response_model=Sprint)
async def create_sprint(
    sprint: SprintCreate,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new sprint"""
    try:
        # Check team existence and permissions
        team = await monday_service.get_team(sprint.team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
            
        if not current_user.is_admin and current_user.id not in [m.id for m in team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create sprint for this team"
            )

        # Convert dates to UTC and validate
        start_date = datetime.combine(sprint.start_date, datetime.min.time(), tzinfo=pytz.UTC)
        end_date = datetime.combine(sprint.end_date, datetime.max.time(), tzinfo=pytz.UTC)
        
        validate_sprint_dates(start_date, end_date, sprint.team_id, monday_service)
        await check_sprint_overlap(sprint.team_id, start_date, end_date, monday_service)

        # Get AI suggestions for sprint planning
        tasks = await monday_service.get_team_tasks(sprint.team_id, status="todo")
        
        # Create sprint in Monday.com
        sprint_data = sprint.dict()
        sprint_data['created_by'] = current_user.id
        sprint_data['created_at'] = datetime.now(pytz.UTC)
        sprint_data['start_date'] = start_date
        sprint_data['end_date'] = end_date
        
        created_sprint = await monday_service.create_sprint(sprint_data)
        
        # Send sprint creation notification
        if team.slack_channel_id:
            try:
                await slack_service.send_message(
                    channel=team.slack_channel_id,
                    text=f"🎯 New Sprint Created: {sprint.name}\nGoal: {sprint.goal}\n"
                         f"Duration: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                )
            except Exception as slack_error:
                # Log the error but don't fail the sprint creation
                print(f"Failed to send Slack notification: {str(slack_error)}")
        
        return created_sprint
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sprint: {str(e)}"
        )

@router.get("/{sprint_id}", response_model=Sprint)
async def get_sprint(
    sprint_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific sprint by ID"""
    try:
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this sprint"
            )
            
        return sprint
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sprint: {str(e)}"
        )

@router.put("/{sprint_id}", response_model=Sprint)
async def update_sprint(
    sprint_id: str,
    sprint_update: SprintUpdate,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Update a sprint"""
    try:
        # Get existing sprint
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this sprint"
            )

        # Validate and convert dates if being updated
        if sprint_update.start_date or sprint_update.end_date:
            start_date = datetime.combine(
                sprint_update.start_date or sprint.start_date,
                datetime.min.time(),
                tzinfo=pytz.UTC
            )
            end_date = datetime.combine(
                sprint_update.end_date or sprint.end_date,
                datetime.max.time(),
                tzinfo=pytz.UTC
            )
            
            validate_sprint_dates(start_date, end_date, sprint.team_id, monday_service)
            await check_sprint_overlap(sprint.team_id, start_date, end_date, monday_service)
            
            sprint_update.start_date = start_date
            sprint_update.end_date = end_date

        updated_sprint = await monday_service.update_sprint(
            sprint_id,
            sprint_update.model_dump(exclude_unset=True)
        )
        return updated_sprint
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sprint: {str(e)}"
        )

@router.post("/{sprint_id}/start")
async def start_sprint(
    sprint_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(get_current_user)
):
    """Start a sprint"""
    try:
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to start this sprint"
            )
        
        if sprint.status != SprintStatus.PLANNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sprint is not in planning state"
            )
            
        # Check if start date is in the future
        now = datetime.now(pytz.UTC)
        if sprint.start_date > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start a sprint before its start date"
            )
        
        # Update sprint status
        updated_sprint = await monday_service.update_sprint(
            sprint_id,
            {"status": SprintStatus.IN_PROGRESS}
        )
        
        # Send sprint start notification
        if sprint.team.slack_channel_id:
            try:
                await slack_service.send_sprint_report({
                    "name": sprint.name,
                    "goal": sprint.goal,
                    "start_date": sprint.start_date,
                    "end_date": sprint.end_date,
                    "tasks": sprint.tasks
                })
            except Exception as slack_error:
                # Log the error but don't fail the sprint start
                print(f"Failed to send Slack notification: {str(slack_error)}")
        
        return {"message": "Sprint started successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sprint: {str(e)}"
        )

@router.post("/{sprint_id}/complete")
async def complete_sprint(
    sprint_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    slack_service: SlackService = Depends(get_slack_service),
    current_user: User = Depends(get_current_user)
):
    """Complete a sprint"""
    try:
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to complete this sprint"
            )
        
        if sprint.status != SprintStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sprint is not in progress"
            )
            
        # Check if end date has passed
        now = datetime.now(pytz.UTC)
        if now < sprint.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete a sprint before its end date"
            )
        
        # Generate sprint completion report
        completion_data = await monday_service.generate_sprint_completion_data(sprint_id)
        
        
        # Update sprint status and metrics
        updated_sprint = await monday_service.update_sprint(
            sprint_id,
            {
                "status": SprintStatus.COMPLETED,
                "velocity": completion_data["velocity"],
                "completed_points": completion_data["completed_points"],
                "completed_at": now
            }
        )
        
        # Send sprint completion report
        if sprint.team.slack_channel_id:
            try:
                await slack_service.send_sprint_report({
                    **completion_data,
                })
            except Exception as slack_error:
                # Log the error but don't fail the sprint completion
                print(f"Failed to send Slack notification: {str(slack_error)}")
        
        return {
            "message": "Sprint completed successfully",
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete sprint: {str(e)}"
        )

@router.get("/{sprint_id}/metrics")
async def get_sprint_metrics(
    sprint_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get sprint metrics and analytics"""
    try:
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this sprint's metrics"
            )
            
        metrics = await monday_service.get_sprint_metrics(sprint_id)
        return metrics
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sprint metrics: {str(e)}"
        )

@router.post("/{sprint_id}/tasks/{task_id}")
async def add_task_to_sprint(
    sprint_id: str,
    task_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Add a task to the sprint"""
    try:
        # Get sprint and task
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        task = await monday_service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this sprint"
            )
            
        # Validate sprint status
        if sprint.status == SprintStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add tasks to a completed sprint"
            )
            
        # Check if task belongs to the same team
        if task.team_id != sprint.team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task does not belong to the sprint's team"
            )
            
        # Check if task is already in another active sprint
        current_sprint = await monday_service.get_task_sprint(task_id)
        if current_sprint and current_sprint.id != sprint_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is already assigned to another sprint"
            )

        updated_sprint = await monday_service.add_task_to_sprint(sprint_id, task_id)
        return {"message": "Task added to sprint successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add task to sprint: {str(e)}"
        )

@router.delete("/{sprint_id}/tasks/{task_id}")
async def remove_task_from_sprint(
    sprint_id: str,
    task_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Remove a task from the sprint"""
    try:
        # Get sprint and task
        sprint = await monday_service.get_sprint(sprint_id)
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint not found"
            )
            
        task = await monday_service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in sprint.team.members]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this sprint"
            )
            
        # Validate sprint status
        if sprint.status == SprintStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove tasks from a completed sprint"
            )
            
        # Check if task is in this sprint
        if task.sprint_id != sprint_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is not in this sprint"
            )

        updated_sprint = await monday_service.remove_task_from_sprint(sprint_id, task_id)
        return {"message": "Task removed from sprint successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove task from sprint: {str(e)}"
        ) 