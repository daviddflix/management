"""This file exports all the routers from the endpoints package."""

from .auth import router as auth_router
from .users import router as users_router
from .teams import router as teams_router
from .tasks import router as tasks_router
from .sprints import router as sprints_router
from .messages import router as messages_router
from .notifications import router as notifications_router
from .boards import router as boards_router

# Export all routers
__all__ = [
    "auth_router",
    "users_router",
    "teams_router",
    "tasks_router",
    "sprints_router",
    "messages_router",
    "notifications_router",
    "boards_router"
]