from fastapi_sessions.backends.implementations import RedisBackend
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier
from uuid import UUID
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.models.auth import SessionData
import redis
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

# Redis client for session storage
redis_client = redis.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    decode_responses=True
)

# Cookie parameters with security settings
cookie_params = CookieParameters(
    name=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_EXPIRE_MINUTES * 60,
    httponly=settings.SESSION_COOKIE_HTTPONLY,
    secure=settings.SESSION_COOKIE_SECURE,
    samesite=settings.SESSION_COOKIE_SAMESITE,
    domain=None,  # Set in production
    path="/"
)

# Redis backend for session storage
class CustomRedisBackend(RedisBackend[UUID, SessionData]):
    async def create(self, session_id: UUID, data: SessionData) -> None:
        """Create a new session."""
        try:
            await self.redis.setex(
                str(session_id),
                settings.SESSION_EXPIRE_MINUTES * 60,
                json.dumps(data.dict())
            )
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            raise

    async def read(self, session_id: UUID) -> Optional[SessionData]:
        """Read session data."""
        try:
            data = await self.redis.get(str(session_id))
            if not data:
                return None
            return SessionData(**json.loads(data))
        except Exception as e:
            logger.error(f"Session read error: {str(e)}")
            return None

    async def update(self, session_id: UUID, data: SessionData) -> None:
        """Update session data."""
        await self.create(session_id, data)

    async def delete(self, session_id: UUID) -> None:
        """Delete a session."""
        try:
            await self.redis.delete(str(session_id))
        except Exception as e:
            logger.error(f"Session deletion error: {str(e)}")
            raise

backend = CustomRedisBackend(redis_client)

# Session cookie management
cookie = SessionCookie(
    cookie_name=cookie_params.name,
    identifier="general_verifier",
    auto_error=True,
    secret_key=settings.SESSION_SECRET_KEY,
    cookie_params=cookie_params
)

class SessionVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: CustomRedisBackend,
        auth_http_exception: Exception,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    async def verify_session(self, model: SessionData) -> bool:
        """Verify the session data."""
        try:
            now = datetime.now(timezone.utc)
            # Check if session is expired
            if model.expires_at < now:
                return False
            
            # Check if user is still active
            if not model.is_active:
                return False
                
            # Extend session if needed
            if model.should_refresh():
                model.expires_at = now + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
                await self.backend.update(model.session_id, model)
                
            return True
        except Exception as e:
            logger.error(f"Session verification error: {str(e)}")
            return False

# Create session verifier instance
verifier = SessionVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=Exception
) 