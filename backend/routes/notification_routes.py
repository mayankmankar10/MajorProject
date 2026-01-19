# backend/routes/notification_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Notification, User
from backend.notifications.connection_manager import manager
from backend.utils.auth import decode_access_token, get_current_user
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# Pydantic models
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    action_url: Optional[str]
    metadata: Optional[dict]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z' if v else None
        }


class MarkReadRequest(BaseModel):
    notification_ids: List[int]


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time notifications."""
    
    # Verify token and get user_id
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    user_id = payload.get("user_id")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return
    
    # Connect user
    await manager.connect(user_id, websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages (heartbeat/ping-pong)
            data = await websocket.receive_text()
            
            # Handle ping
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    current_user: dict = Depends(get_current_user),
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get user's notifications."""
    
    user_id = current_user.get("user_id")
    query = db.query(Notification).filter(Notification.recipient_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
    
    # Manually construct response to handle metadata field correctly
    return [
        NotificationResponse(
            id=n.id,
            title=n.title,
            message=n.message,
            notification_type=n.notification_type,
            action_url=n.action_url,
            metadata=n.meta_data or {},  # Use meta_data column and default to empty dict
            is_read=n.is_read,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.get("/unread-count")
def get_unread_count(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get count of unread notifications."""
    
    user_id = current_user.get("user_id")
    
    count = db.query(Notification).filter(
        Notification.recipient_id == user_id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.post("/mark-read")
def mark_notifications_read(
    request: MarkReadRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notifications as read."""
    
    user_id = current_user.get("user_id")
    
    try:
        db.query(Notification).filter(
            Notification.id.in_(request.notification_ids),
            Notification.recipient_id == user_id
        ).update(
            {"is_read": True, "read_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        
        return {"status": "success", "marked_count": len(request.notification_ids)}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking notifications read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")


@router.post("/mark-all-read")
def mark_all_read(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark all user's notifications as read."""
    
    user_id = current_user.get("user_id")
    
    try:
        updated = db.query(Notification).filter(
            Notification.recipient_id == user_id,
            Notification.is_read == False
        ).update(
            {"is_read": True, "read_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        
        return {"status": "success", "marked_count": updated}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking all notifications read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    
    user_id = current_user.get("user_id")
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"status": "success", "message": "Notification deleted"}


@router.get("/active-connections")
def get_active_connections():
    """Get count and list of active WebSocket connections (admin/debug endpoint)."""
    return {
        "count": manager.get_connected_count(),
        "connected_users": manager.get_connected_users()
    }
