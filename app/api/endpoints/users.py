from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from app.models.user import User, UserCreate, UserUpdate, UserRole, UserStatus
from app.services.monday_service import MondayService
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, get_current_user, check_permissions
from app.core.deps import get_monday_service, get_redis_service
from app.services.redis_service import RedisService
import re

router = APIRouter()

def validate_password(password: str) -> bool:
    """
    Validate password strength
    - At least 8 characters
    - Contains uppercase and lowercase letters
    - Contains numbers
    - Contains special characters
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

@router.get("/", response_model=List[User])
async def get_users(
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    team_id: Optional[str] = None,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Get all users with optional filtering (requires admin or tech lead role)"""
    try:
        users = await monday_service.get_users(role=role, status=status, team_id=team_id)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(check_permissions(["admin"]))
):
    """Create a new user (requires admin role)"""
    try:
        # Validate email
        try:
            valid = validate_email(user.email)
            user.email = valid.email
        except EmailNotValidError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address"
            )

        # Check if email already exists
        existing_user = await monday_service.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        if not validate_password(user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters"
            )
        
        # Hash password
        hashed_password = get_password_hash(user.password)
        
        # Create user in Monday.com
        user_data = user.dict()
        user_data.pop('password')
        user_data['hashed_password'] = hashed_password
        user_data['created_at'] = datetime.utcnow()
        user_data['last_login'] = None
        
        created_user = await monday_service.create_user(user_data)
        return created_user
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    try:
        user = await monday_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Check permissions
        if not current_user.is_admin and current_user.id != user_id:
            if not any(team.id in [t.id for t in current_user.teams] for team in user.teams):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this user"
                )
                
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    try:
        # Check permissions
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )

        # Get existing user
        existing_user = await monday_service.get_user(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Validate email if being updated
        if user_update.email:
            try:
                valid = validate_email(user_update.email)
                user_update.email = valid.email
            except EmailNotValidError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email address"
                )

            # Check if new email already exists
            if user_update.email != existing_user.email:
                existing_email = await monday_service.get_user_by_email(user_update.email)
                if existing_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )

        # Validate password if being updated
        if user_update.password:
            if not validate_password(user_update.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters"
                )
            user_update.hashed_password = get_password_hash(user_update.password)
            user_update.password = None  # Don't store plain password

        # Only admin can update role
        if user_update.role and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update user roles"
            )

        updated_user = await monday_service.update_user(
            user_id,
            user_update.dict(exclude_unset=True, exclude={'password'})
        )
        return updated_user
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.get("/{user_id}/tasks", response_model=List[str])
async def get_user_tasks(
    user_id: str,
    status: Optional[str] = None,
    sprint_id: Optional[str] = None,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks assigned to a user"""
    try:
        # Check permissions
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's tasks"
            )

        tasks = await monday_service.get_user_tasks(
            user_id,
            status=status,
            sprint_id=sprint_id
        )
        return tasks
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user tasks: {str(e)}"
        )

@router.post("/{user_id}/status")
async def update_user_status(
    user_id: str,
    status: UserStatus,
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(check_permissions(["admin", "tech_lead"]))
):
    """Update user status (active/inactive/on_leave) (requires admin or tech lead role)"""
    try:
        # Get existing user
        existing_user = await monday_service.get_user(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await monday_service.update_user_status(user_id, status)
        return {"message": "Status updated successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}"
        )

@router.get("/{user_id}/performance", response_model=dict)
async def get_user_performance(
    user_id: str,
    time_period: Optional[str] = Query(
        "last_sprint",
        regex="^(last_sprint|last_month|last_quarter|last_year)$"
    ),
    monday_service: MondayService = Depends(get_monday_service),
    current_user: User = Depends(get_current_user)
):
    """Get user performance metrics"""
    try:
        # Get user and check existence
        user = await monday_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check permissions
        if not current_user.is_admin and current_user.id != user_id:
            if not any(team.id in [t.id for t in current_user.teams] for team in user.teams):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this user's performance"
                )

        performance = await monday_service.get_user_performance(user_id, time_period)
        return performance
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user performance: {str(e)}"
        ) 