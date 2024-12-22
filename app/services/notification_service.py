from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
from enum import Enum
import logging

from app.models.notification import Notification, NotificationCreate, NotificationResponse
from app.services.websocket_service import notification_manager

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    TASK = "task"
    MENTION = "mention"
    SYSTEM = "system"
    ALERT = "alert"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        notification: NotificationCreate,
        send_websocket: bool = True
    ) -> Notification:
        """
        Create a new notification and optionally send it through WebSocket.
        
        Args:
            notification: The notification data
            send_websocket: Whether to send real-time notification via WebSocket
        """
        try:
            db_notification = Notification(
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                type=notification.type,
                created_at=datetime.utcnow()
            )
            
            self.db.add(db_notification)
            await self.db.commit()
            await self.db.refresh(db_notification)
            
            if send_websocket:
                await self._send_websocket_notification(db_notification)
                
            return db_notification
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification: {str(e)}")
            raise

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None
    ) -> List[Notification]:
        """
        Get user notifications with filtering options.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            unread_only: Whether to return only unread notifications
            notification_type: Filter by notification type
        """
        try:
            query = select(Notification).where(Notification.user_id == user_id)
            
            if unread_only:
                query = query.where(Notification.is_read == False)
                
            if notification_type:
                query = query.where(Notification.type == notification_type)
                
            query = query.order_by(Notification.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            raise

    async def mark_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Notification:
        """Mark a notification as read."""
        try:
            query = (
                select(Notification)
                .where(Notification.id == notification_id)
                .where(Notification.user_id == user_id)
            )
            
            result = await self.db.execute(query)
            notification = result.scalar_one_or_none()
            
            if not notification:
                raise Exception(f"Notification {notification_id} not found")
                
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(notification)
            
            return notification
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking notification as read: {str(e)}")
            raise

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all user's notifications as read."""
        try:
            query = (
                update(Notification)
                .where(Notification.user_id == user_id)
                .where(Notification.is_read == False)
                .values(is_read=True, read_at=datetime.utcnow())
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking all notifications as read: {str(e)}")
            raise

    async def delete_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """Delete a specific notification."""
        try:
            query = (
                delete(Notification)
                .where(Notification.id == notification_id)
                .where(Notification.user_id == user_id)
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting notification: {str(e)}")
            raise

    async def delete_all_read(self, user_id: str) -> int:
        """Delete all read notifications for a user."""
        try:
            query = (
                delete(Notification)
                .where(Notification.user_id == user_id)
                .where(Notification.is_read == True)
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting read notifications: {str(e)}")
            raise

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        try:
            query = (
                select(Notification)
                .where(Notification.user_id == user_id)
                .where(Notification.is_read == False)
            )
            
            result = await self.db.execute(query)
            return len(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            raise

    async def _send_websocket_notification(self, notification: Notification):
        """Send notification through WebSocket."""
        try:
            notification_data = {
                "id": str(notification.id),
                "title": notification.title,
                "message": notification.message,
                "type": notification.type,
                "created_at": notification.created_at.isoformat()
            }
            
            await notification_manager.send_notification(
                str(notification.user_id),
                notification_data
            )
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {str(e)}")
            # Don't raise the exception as this is a non-critical operation

# Create a function to get the service instance
async def get_notification_service(db: AsyncSession) -> NotificationService:
    return NotificationService(db)
