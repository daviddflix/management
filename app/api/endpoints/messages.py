from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import UserResponse
from app.models.message import MessageCreate, MessageResponse, MessageThread
from app.services.message_service import MessageService
from app.services.websocket_service import communication_manager

router = APIRouter()

@router.websocket("/channel/{channel_id}")
async def channel_websocket(websocket: WebSocket, channel_id: str, user_id: str):
    """WebSocket endpoint for real-time channel messages."""
    await communication_manager.connect_to_channel(websocket, channel_id, user_id)
    try:
        while True:
            # Wait for any message from the client
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        communication_manager.disconnect_from_channel(websocket, channel_id, user_id)

@router.post("/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new message in a channel."""
    service = MessageService(db)
    db_message = await service.create_message(message, current_user.id)
    
    # Send real-time message through WebSocket
    await communication_manager.send_channel_message(
        message.channel_id,
        {
            "id": db_message.id,
            "content": db_message.content,
            "sender_id": db_message.sender_id,
            "attachments": db_message.attachments,
            "created_at": db_message.created_at.isoformat()
        }
    )
    return db_message

@router.get("/channel/{channel_id}", response_model=List[MessageResponse])
async def get_channel_messages(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all messages in a channel."""
    service = MessageService(db)
    return await service.get_channel_messages(channel_id)

@router.get("/thread/{message_id}", response_model=MessageThread)
async def get_message_thread(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a message thread (parent message and all replies)."""
    service = MessageService(db)
    return await service.get_message_thread(message_id)

@router.post("/{message_id}/reaction")
async def add_reaction(
    message_id: str,
    reaction: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Add a reaction to a message."""
    service = MessageService(db)
    await service.add_reaction(message_id, current_user.id, reaction)
    return {"status": "success"}

@router.delete("/{message_id}/reaction/{reaction}")
async def remove_reaction(
    message_id: str,
    reaction: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Remove a reaction from a message."""
    service = MessageService(db)
    await service.remove_reaction(message_id, current_user.id, reaction)
    return {"status": "success"}
