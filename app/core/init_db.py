from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import init_db, get_db
from app.core.config import settings
from app.models.user import UserRole
from app.models.database.user import DBUser
from app.core.security import get_password_hash
import logging
import asyncio
from typing import AsyncGenerator
import alembic.config
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def create_first_superuser(session: AsyncSession) -> None:
    """Create the first superuser if it doesn't exist."""
    try:
        # Check if superuser exists
        superuser = await session.get(DBUser, settings.FIRST_SUPERUSER_EMAIL)
        
        if not superuser:
            superuser = DBUser(
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                name="Admin",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(superuser)
            await session.commit()
            logger.info("First superuser created successfully")
    except Exception as e:
        logger.error(f"Error creating superuser: {str(e)}")
        raise

async def run_migrations() -> None:
    """Run database migrations using alembic."""
    try:
        alembic_args = [
            '--raiseerr',
            'upgrade', 'head',
        ]
        alembic.config.main(argv=alembic_args)
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise

async def init_application() -> None:
    """Initialize the application database and create first superuser."""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Run migrations
        await run_migrations()
        
        # Create first superuser
        async with get_db() as session:
            await create_first_superuser(session)
            
        logger.info("Application initialization completed successfully")
    except Exception as e:
        logger.error(f"Application initialization error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_application()) 