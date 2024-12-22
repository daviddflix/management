from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.notification import NotificationCreate, NotificationResponse
from app.services.notification_service import NotificationService
from app.services.websocket_service import manager

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Wait for any message from the client
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    db_notification = service.create_notification(notification)
    
    # Send real-time notification through WebSocket
    await manager.send_personal_notification(
        notification.user_id,
        {
            "id": db_notification.id,
            "title": db_notification.title,
            "message": db_notification.message,
            "type": db_notification.type
        }
    )
    return db_notification

@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(
    user_id: int,
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    return service.get_user_notifications(user_id)

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    notification = service.mark_as_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    if not service.delete_notification(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}
