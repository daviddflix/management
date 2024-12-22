from typing import Dict, Set, Optional, List, Union
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WSMessageType(str, Enum):
    # Communication types
    CHANNEL_MESSAGE = "channel_message"
    DIRECT_MESSAGE = "direct_message"
    CHANNEL_EVENT = "channel_event"
    REACTION = "reaction"
    MESSAGE_UPDATE = "message_update"
    MESSAGE_DELETE = "message_delete"
    CHANNEL_UPDATE = "channel_update"
    USER_TYPING = "user_typing"
    USER_PRESENCE = "user_presence"
    
    # Notification types
    NOTIFICATION = "notification"
    TASK_UPDATE = "task_update"
    MENTION = "mention"
    ALERT = "alert"
    SYSTEM = "system"

class WSConnectionType(str, Enum):
    USER = "user"
    CHANNEL = "channel"
    TEAM = "team"

class BaseConnectionManager:
    """Base class for WebSocket connection management."""
    
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}
        
    async def _send_message(self, connection: WebSocket, message: dict):
        """Helper method to send a message with error handling."""
        try:
            await connection.send_json(message)
            return True
        except WebSocketDisconnect:
            logger.warning("Failed to send message due to disconnection")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

class CommunicationManager(BaseConnectionManager):
    """Manages WebSocket connections for real-time communication (channels, messages)."""
    
    def __init__(self):
        super().__init__()
        self.channel_connections: Dict[str, Set[WebSocket]] = {}
        self.team_connections: Dict[str, Set[WebSocket]] = {}
        self.channel_presence: Dict[str, Set[str]] = {}
        self.user_status: Dict[str, datetime] = {}
        
    async def connect_to_channel(self, websocket: WebSocket, channel_id: str, user_id: str):
        """Connect a user to a channel."""
        await websocket.accept()
        if channel_id not in self.channel_connections:
            self.channel_connections[channel_id] = set()
            self.channel_presence[channel_id] = set()
        self.channel_connections[channel_id].add(websocket)
        self.channel_presence[channel_id].add(user_id)
        await self.broadcast_channel_event(channel_id, "user_joined", {"user_id": user_id})
        
    def disconnect_from_channel(self, websocket: WebSocket, channel_id: str, user_id: str):
        """Disconnect a user from a channel."""
        if channel_id in self.channel_connections:
            self.channel_connections[channel_id].discard(websocket)
            self.channel_presence[channel_id].discard(user_id)
            if not self.channel_connections[channel_id]:
                del self.channel_connections[channel_id]
                del self.channel_presence[channel_id]
                
    async def send_channel_message(self, channel_id: str, message: dict):
        """Send a message to a channel."""
        formatted_message = {
            "type": WSMessageType.CHANNEL_MESSAGE,
            "data": message,
            "channel_id": channel_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_channel(channel_id, formatted_message)
        
    async def broadcast_to_channel(self, channel_id: str, message: dict):
        """Broadcast a message to all users in a channel."""
        if channel_id in self.channel_connections:
            disconnected = set()
            for connection in self.channel_connections[channel_id]:
                success = await self._send_message(connection, message)
                if not success:
                    disconnected.add(connection)
            # Clean up disconnected connections
            for conn in disconnected:
                self.channel_connections[channel_id].discard(conn)
                
    async def broadcast_channel_event(self, channel_id: str, event_type: str, data: dict):
        """Broadcast a channel event."""
        message = {
            "type": WSMessageType.CHANNEL_EVENT,
            "event": event_type,
            "data": data,
            "channel_id": channel_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_channel(channel_id, message)

    def get_channel_presence(self, channel_id: str) -> Set[str]:
        """Get the set of users present in a channel."""
        return self.channel_presence.get(channel_id, set())


class NotificationManager(BaseConnectionManager):
    """Manages WebSocket connections for notifications."""
    
    def __init__(self):
        super().__init__()
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """Connect a user for notifications."""
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Disconnect a user from notifications."""
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                
    async def send_notification(self, user_id: str, notification: dict, notification_type: WSMessageType = WSMessageType.NOTIFICATION):
        """Send a notification to a user."""
        message = {
            "type": notification_type,
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(user_id, message)
        
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections of a user."""
        if user_id in self.user_connections:
            disconnected = set()
            for connection in self.user_connections[user_id]:
                success = await self._send_message(connection, message)
                if not success:
                    disconnected.add(connection)
            # Clean up disconnected connections
            for conn in disconnected:
                self.user_connections[user_id].discard(conn)
                
    async def broadcast_system_notification(self, notification: dict):
        """Broadcast a system notification to all connected users."""
        message = {
            "type": WSMessageType.SYSTEM,
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        for connections in self.user_connections.values():
            for connection in connections:
                await self._send_message(connection, message)

# Create global instances
communication_manager = CommunicationManager()
notification_manager = NotificationManager()
