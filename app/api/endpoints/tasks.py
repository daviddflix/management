from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from app.models.task import Task, TaskCreate, TaskUpdate, TaskStatus
from app.services.monday_service import MondayService
from app.core.config import settings
from app.core.security import get_current_user, check_permissions
from app.models.user import User
from app.core.deps import get_monday_service, get_openai_service
from app.services.redis_service import RedisService
from app.core.deps import get_redis_service

router = APIRouter()

@router.get("/", response_model=List[Task])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    assignee: Optional[str] = None,
    sprint_id: Optional[str] = None,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks with optional filtering
    """
    try:
        tasks = await monday_service.get_tasks(
            status=status,
            assignee=assignee,
            sprint_id=sprint_id
        )
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )

@router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new task (requires authentication)"""
    try:
        # Validate task data
        if task.story_points and task.story_points < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Story points cannot be negative"
            )
            
        if task.sprint_id:
            sprint = await monday_service.get_sprint(task.sprint_id)
            if not sprint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sprint not found"
                )

        task.created_by = current_user.id
        created_task = await monday_service.create_task(task)
        return created_task
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific task by ID
    """
    try:
        task = await monday_service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
            
        # Check permissions
        if not current_user.is_admin and task.created_by != current_user.id:
            if not any(team.id == task.team_id for team in current_user.teams):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this task"
                )
                
        return task
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task: {str(e)}"
        )

@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task
    """
    try:
        # Get existing task
        existing_task = await monday_service.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
            
        # Check permissions
        if not current_user.is_admin and existing_task.created_by != current_user.id:
            if not any(team.id == existing_task.team_id for team in current_user.teams):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this task"
                )

        # Validate status transition
        if task_update.status:
            valid_transitions = {
                TaskStatus.TODO: [TaskStatus.IN_PROGRESS],
                TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW, TaskStatus.DONE],
                TaskStatus.REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.DONE],
                TaskStatus.DONE: [TaskStatus.IN_PROGRESS]
            }
            
            if (existing_task.status != task_update.status and 
                task_update.status not in valid_transitions.get(existing_task.status, [])):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition from {existing_task.status} to {task_update.status}"
                )

        updated_task = await monday_service.update_task(task_id, task_update)
        return updated_task
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Delete a task (requires admin or tech lead role)"""
    try:
        # Get existing task
        existing_task = await monday_service.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
            
        success = await monday_service.delete_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task"
            )
            
        return {"message": "Task deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )
