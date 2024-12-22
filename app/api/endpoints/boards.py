from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from enum import Enum

from app.models.board import Board, BoardCreate, BoardUpdate, BoardResponse, BoardSummary
from app.models.user import User, UserResponse
from app.models.team import Team
from app.models.activity import Activity
from app.core.security import get_current_user, check_permissions
from app.core.deps import get_db, get_redis_service
from app.services.redis_service import RedisService
from sqlalchemy.ext.asyncio import AsyncSession

class BoardVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM = "team"

router = APIRouter()

@router.get("/", response_model=List[BoardSummary])
async def get_boards(
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis_service),
    current_user: User = Depends(get_current_user),
    team_id: Optional[str] = None,
    visibility: Optional[BoardVisibility] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get all boards with optional filtering.
    Supports pagination and caching.
    """
    try:
        # Validate team_id if provided
        if team_id:
            team = await db.get(Team, team_id)
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")

        # Try to get from cache first
        cache_key = f"boards:list:{team_id}:{visibility}:{skip}:{limit}"
        cached_data = await redis.get_json(cache_key)
        if cached_data:
            return cached_data

        # Query database
        query = select(Board)
        if team_id:
            query = query.filter(Board.team_id == team_id)
        if visibility:
            query = query.filter(Board.visibility == visibility)
            
        # Add user-specific filters
        if not current_user.is_admin:
            query = query.filter(
                or_(
                    Board.visibility == BoardVisibility.PUBLIC,
                    Board.team_id.in_([team.id for team in current_user.teams]),
                    Board.owner_id == current_user.id
                )
            )
            
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        boards = result.scalars().all()
        
        response = [BoardSummary.model_validate(board) for board in boards]
        
        # Cache the results
        await redis.set_json(cache_key, response, expire=300)  # Cache for 5 minutes
        
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=BoardResponse)
async def create_board(
    board: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new board."""
    try:
        # Validate board visibility
        if not hasattr(BoardVisibility, board.visibility.upper()):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid visibility value. Must be one of: {', '.join([v.value for v in BoardVisibility])}"
            )

        # Validate team membership if team_id is provided
        if board.team_id:
            team = await db.get(Team, board.team_id)
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            if not current_user.is_admin and current_user.id not in [m.id for m in team.members]:
                raise HTTPException(
                    status_code=403,
                    detail="You must be a team member to create a board for this team"
                )

            # Validate board visibility for team boards
            if board.visibility != BoardVisibility.TEAM:
                raise HTTPException(
                    status_code=400,
                    detail="Boards associated with a team must have 'team' visibility"
                )

        db_board = Board(
            **board.model_dump(),
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        
        db.add(db_board)
        
        # Create initial activity log
        activity = Activity(
            board_id=db_board.id,
            user_id=current_user.id,
            action="created",
            details="Board created",
            created_at=datetime.now()
        )
        db.add(activity)
        
        await db.commit()
        await db.refresh(db_board)
        
        return BoardResponse.model_validate(db_board)
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: int = Path(..., description="The ID of the board to get"),
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific board by ID."""
    try:
        # Try to get from cache
        cache_key = f"board:{board_id}"
        cached_data = await redis.get_json(cache_key)
        if cached_data:
            return cached_data

        board = await db.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        # Check permissions
        if not current_user.is_admin and board.visibility != "public":
            if board.owner_id != current_user.id and (
                not board.team_id or 
                current_user.id not in [m.id for m in board.team.members]
            ):
                raise HTTPException(status_code=403, detail="Not authorized to view this board")

        response = BoardResponse.model_validate(board)
        
        # Cache the result
        await redis.set_json(cache_key, response.dict(), expire=300)
        
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: int,
    board_update: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis_service),
    current_user: User = Depends(get_current_user)
):
    """Update a board."""
    try:
        board = await db.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        # Check permissions
        if not current_user.is_admin and board.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this board")

        # Update fields
        for field, value in board_update.dict(exclude_unset=True).items():
            setattr(board, field, value)
            
        board.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(board)
        
        # Invalidate cache
        await redis.delete(f"board:{board_id}")
        await redis.delete_pattern("boards:list:*")
        
        return BoardResponse.model_validate(board)
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{board_id}")
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis_service),
    current_user: User = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Delete a board (requires admin or tech lead role)."""
    try:
        board = await db.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        # Check permissions
        if not current_user.is_admin and board.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this board")

        await db.delete(board)
        await db.commit()
        
        # Invalidate cache
        await redis.delete(f"board:{board_id}")
        await redis.delete_pattern("boards:list:*")
        
        return {"message": "Board deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{board_id}/members", response_model=List[UserResponse])
async def add_board_members(
    board_id: int,
    member_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add members to a board."""
    try:
        board = await db.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        # Check permissions
        if not current_user.is_admin and board.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to add members to this board")

        # Get users
        users = await db.execute(select(User).where(User.id.in_(member_ids)))
        users = users.scalars().all()
        
        # Add members
        board.members.extend([u for u in users if u not in board.members])
        
        await db.commit()
        await db.refresh(board)
        
        return [UserResponse.from_orm(member) for member in board.members]
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{board_id}/members/{user_id}")
async def remove_board_member(
    board_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a board."""
    try:
        board = await db.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        # Check permissions
        if not current_user.is_admin and board.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to remove members from this board")

        # Remove member
        board.members = [m for m in board.members if m.id != user_id]
        
        await db.commit()
        
        return {"message": "Member removed successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{board_id}/activity", response_model=List[dict])
async def get_board_activity(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get board activity log."""
    try:
        board = await db.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        # Check permissions
        if not current_user.is_admin and board.visibility != "public":
            if board.owner_id != current_user.id and (
                not board.team_id or 
                current_user.id not in [m.id for m in board.team.members]
            ):
                raise HTTPException(status_code=403, detail="Not authorized to view this board's activity")

        # Get activity log
        query = select(Activity).where(Activity.board_id == board_id)
        query = query.order_by(Activity.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        activities = result.scalars().all()
        
        return [activity.to_dict() for activity in activities]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
