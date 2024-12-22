from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal
from app.core.config import settings
from app.services.redis_service import RedisService
from app.services.monday_service import MondayService
from app.services.slack_service import SlackService
from app.services.redis_service import RedisService

# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Redis service dependency
async def get_redis_service():
    redis = RedisService(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB
    )
    try:
        yield redis
    finally:
        await redis.close()

# Monday.com service dependency
async def get_monday_service() -> MondayService:
    if not settings.MONDAY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Monday.com API key not configured"
        )
    return MondayService(api_key=settings.MONDAY_API_KEY)

# Slack service dependency
async def get_slack_service() -> SlackService:
    if not settings.SLACK_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Slack bot token not configured"
        )
    return SlackService(bot_token=settings.SLACK_BOT_TOKEN)

# Cache key generator helper
def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from prefix and kwargs"""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)
