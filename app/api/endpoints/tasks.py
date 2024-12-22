from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskCreate, TaskUpdate, TaskResponse
from app.models.database.task import Task
from app.models.database.user import DBUser
from app.models.database.team import Team
from app.core.security import get_current_user, check_permissions
from app.core.deps import get_db

router = APIRouter()

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
    team_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all tasks with optional filtering."""
    try:
        query = select(Task)
        
        # Apply filters
        if team_id:
            query = query.filter(Task.team_id == team_id)
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
            
        # Add user-specific filters
        if not current_user.is_admin:
            query = query.filter(
                or_(
                    Task.team_id.in_([t.id for t in current_user.teams]),
                    Task.assignee_id == current_user.id,
                    Task.creator_id == current_user.id
                )
            )
            
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return [TaskResponse.model_validate(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Create a new task."""
    try:
        # Validate team membership if team_id is provided
        if task.team_id:
            team = await db.get(Team, task.team_id)
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            if not current_user.is_admin and current_user.id not in [m.id for m in team.members]:
                raise HTTPException(
                    status_code=403,
                    detail="You must be a team member to create a task for this team"
                )

        db_task = Task(
            **task.model_dump(),
            creator_id=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        return TaskResponse.model_validate(db_task)
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Get a specific task by ID."""
    try:
        task = await db.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Check permissions
        if not current_user.is_admin:
            if task.team_id and current_user.id not in [m.id for m in task.team.members]:
                if task.assignee_id != current_user.id and task.creator_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Not authorized to view this task")
            
        return TaskResponse.model_validate(task)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Update a task (requires admin or tech lead role)."""
    try:
        task = await db.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Check permissions
        if not current_user.is_admin:
            if task.team_id and current_user.id not in [m.id for m in task.team.members]:
                raise HTTPException(status_code=403, detail="Not authorized to update this task")

        # Update fields
        for field, value in task_update.dict(exclude_unset=True).items():
            setattr(task, field, value)
            
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        return TaskResponse.model_validate(task)
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Delete a task (requires admin or tech lead role)"""
    try:
        # Get existing task
        existing_task = await db.get(Task, task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
            
        await db.delete(existing_task)
        await db.commit()
            
        return {"message": "Task deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
