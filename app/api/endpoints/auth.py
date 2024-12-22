from fastapi import APIRouter, HTTPException, Depends, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timedelta
from app.models.auth import Token, LoginRequest, RefreshTokenRequest
from app.models.user import UserResponse, UserCreate
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_current_user,
    verify_token,
)
from app.core.config import settings
from app.services.monday_service import MondayService
from app.services.redis_service import RedisService
from app.core.deps import get_redis_service

router = APIRouter()
monday_service = MondayService(settings.MONDAY_API_KEY)

async def check_login_rate_limit(
    email: str,
    redis: RedisService
) -> None:
    """Check if the login attempts for this email are within limits"""
    key = f"login_attempts:{email}"
    attempts = await redis.get(key)
    
    if attempts and int(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {settings.LOGIN_TIMEOUT_MINUTES} minutes"
        )

async def increment_login_attempts(
    email: str,
    redis: RedisService
) -> None:
    """Increment the login attempts counter"""
    key = f"login_attempts:{email}"
    attempts = await redis.get(key)
    
    if not attempts:
        await redis.set(key, "1", expire=settings.LOGIN_TIMEOUT_MINUTES * 60)
    else:
        await redis.incr(key)

async def reset_login_attempts(
    email: str,
    redis: RedisService
) -> None:
    """Reset the login attempts counter after successful login"""
    key = f"login_attempts:{email}"
    await redis.delete(key)

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: LoginRequest,
    redis: RedisService = Depends(get_redis_service)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        # Check rate limiting
        await check_login_rate_limit(form_data.email, redis)
        
        user = await monday_service.get_user_by_email(form_data.email)
        if not user or not verify_password(form_data.password, user.hashed_password):
            # Increment failed attempts
            await increment_login_attempts(form_data.email, redis)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Reset login attempts on successful login
        await reset_login_attempts(form_data.email, redis)

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )

        # Create refresh token if remember_me is True
        refresh_token = None
        if form_data.remember_me:
            refresh_token = create_refresh_token(user.id)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.utcnow() + access_token_expires,
            refresh_token=refresh_token
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    redis: RedisService = Depends(get_redis_service)
):
    """
    Get a new access token using refresh token
    """
    try:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing"
            )

        # Check if token is blacklisted
        if await redis.get(f"blacklisted_token:{refresh_token}"):
            response.delete_cookie("refresh_token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated"
            )

        user_id = verify_token(refresh_token, "refresh")
        if not user_id:
            response.delete_cookie("refresh_token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user = await monday_service.get_user(user_id)
        if not user:
            response.delete_cookie("refresh_token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )

        # Create new refresh token and blacklist the old one
        new_refresh_token = create_refresh_token(user.id)
        await redis.set(
            f"blacklisted_token:{refresh_token}",
            "1",
            expire=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.now() + access_token_expires,
            refresh_token=new_refresh_token
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    redis: RedisService = Depends(get_redis_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Logout user and invalidate refresh token
    """
    try:
        if refresh_token:
            # Blacklist the refresh token
            await redis.set(
                f"blacklisted_token:{refresh_token}",
                "1",
                expire=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )
        response.delete_cookie("refresh_token")
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user 