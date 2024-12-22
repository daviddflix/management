from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from prometheus_client import make_asgi_app
import aioredis

from app.core.config import settings
from app.core.database import init_db
from app.api.endpoints import (
    tasks, sprints, reports, teams, users, auth, metrics,
    channels, messages, notifications, boards
)
from app.services.scheduler_service import scheduler_service
from app.services.monday_service import monday_service
from app.services.slack_service import slack_service
from app.services.websocket_service import (
    communication_manager,
    notification_manager
)

logger = logging.getLogger(__name__)

async def init_redis() -> aioredis.Redis:
    """Initialize Redis connection."""
    try:
        redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )
        # Test connection
        await redis.ping()
        logger.info("Redis connection established")
        return redis
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {str(e)}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    try:
        # Database initialization
        logger.info("Initializing database...")
        await init_db()

        # Initialize Redis
        logger.info("Initializing Redis...")
        app.state.redis = await init_redis()

        # Start scheduler
        logger.info("Starting scheduler service...")
        await scheduler_service.start()

        # Initialize services that need startup
        logger.info("Initializing services...")
        # Add any service initialization here if needed

        logger.info("Application startup complete")
        yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down services...")
        if hasattr(app.state, "redis"):
            await app.state.redis.close()
        await scheduler_service.shutdown()
        logger.info("Shutdown complete")

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/users", tags=["Users"])
    app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
    app.include_router(sprints.router, prefix="/api/sprints", tags=["Sprints"])
    app.include_router(boards.router, prefix="/api/boards", tags=["Boards"])
    app.include_router(channels.router, prefix="/api/channels", tags=["Channels"])
    app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
    app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
    app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])

    return app

app = create_application()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return JSONResponse(
        content={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "description": settings.PROJECT_DESCRIPTION,
            "docs_url": "/api/docs",
            "environment": settings.ENVIRONMENT
        }
    ) 