from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.models.user import User
from app.services.monday_service import MondayService
import aioredis
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increase work factor for better security
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    scheme_name="JWT"
)

# Redis client for token blacklist
redis_client = aioredis.from_url(settings.REDIS_URL)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Create a new refresh token."""
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(
        data={"user_id": user_id, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

async def verify_token(token: str, token_type: str) -> Optional[Dict[str, any]]:
    """Verify and decode a token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        # Check if token is blacklisted
        if await redis_client.get(f"blacklist:{token}"):
            return None
        return payload
    except JWTError as e:
        logger.error(f"Token verification error: {str(e)}")
        return None

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = await verify_token(token, "access")
    if not payload:
        raise credentials_exception
        
    user_id: str = payload.get("user_id")
    if not user_id:
        raise credentials_exception

    try:
        user = await MondayService(settings.MONDAY_API_KEY).get_user(user_id)
        if not user or not user.is_active:
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        raise credentials_exception

def check_permissions(required_roles: list[str]):
    """Check if user has required roles."""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_checker

async def blacklist_token(token: str, expire_time: int) -> None:
    """Add a token to the blacklist."""
    await redis_client.setex(f"blacklist:{token}", expire_time, "true")