from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sprint import SprintCreate, SprintUpdate, SprintResponse, SprintStatus
from app.models.database.sprint import Sprint
from app.models.database.user import DBUser
from app.models.database.team import Team
from app.core.security import get_current_user, check_permissions
from app.core.deps import get_db

router = APIRouter()

@router.get("/", response_model=List[SprintResponse])
async def get_sprints(
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all sprints with optional filtering."""
    try:
        query = select(Sprint)
        
        # Apply filters
        if team_id:
            query = query.filter(Sprint.team_id == team_id)
        if status:
            query = query.filter(Sprint.status == status)
            
        # Add user-specific filters
        if not current_user.is_admin:
            query = query.filter(Sprint.team_id.in_([t.id for t in current_user.teams]))
            
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        sprints = result.scalars().all()
        
        return [SprintResponse.model_validate(sprint) for sprint in sprints]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SprintResponse)
async def create_sprint(
    sprint: SprintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Create a new sprint."""
    try:
        # Validate team
        team = await db.get(Team, sprint.team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        # Check permissions
        if not current_user.is_admin and current_user.id not in [m.id for m in team.members]:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create sprints for this team"
            )
            
        db_sprint = Sprint(**sprint.model_dump())
        db.add(db_sprint)
        await db.commit()
        await db.refresh(db_sprint)
        
        return SprintResponse.model_validate(db_sprint)
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sprint_id}", response_model=SprintResponse)
async def get_sprint(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Get a specific sprint by ID."""
    try:
        sprint = await db.get(Sprint, sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
            
        # Check permissions
        if not current_user.is_admin:
            if sprint.team_id not in [t.id for t in current_user.teams]:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to view this sprint"
                )
                
        return SprintResponse.model_validate(sprint)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sprint_id}", response_model=SprintResponse)
async def update_sprint(
    sprint_id: str,
    sprint_update: SprintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Update a sprint."""
    try:
        sprint = await db.get(Sprint, sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
            
        # Check permissions
        if not current_user.is_admin:
            if sprint.team_id not in [t.id for t in current_user.teams]:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to update this sprint"
                )
                
        # Update fields
        for field, value in sprint_update.model_dump(exclude_unset=True).items():
            setattr(sprint, field, value)
            
        sprint.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(sprint)
        
        return SprintResponse.model_validate(sprint)
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{sprint_id}")
async def delete_sprint(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Delete a sprint."""
    try:
        sprint = await db.get(Sprint, sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
            
        # Check permissions
        if not current_user.is_admin:
            if sprint.team_id not in [t.id for t in current_user.teams]:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to delete this sprint"
                )
                
        await db.delete(sprint)
        await db.commit()
        
        return {"message": "Sprint deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 