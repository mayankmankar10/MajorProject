# backend/tools_langchain/notification_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Notification
from backend.notifications.connection_manager import manager
import json
import logging

logger = logging.getLogger(__name__)

class NotificationToolInput(BaseModel):
    """Input schema for NotificationTool."""
    user_id: int = Field(description="User ID to send notification to")
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message content")
    notification_type: str = Field(description="Type: job_match, interview, application, or onboarding")
    action_url: str = Field(default="", description="Optional URL to navigate to")

class NotificationTool(BaseTool):
    """
    Sends push notifications to users via WebSocket and stores in database.
    """
    name: str = "NotificationTool"
    description: str = """
    Sends real-time notifications to users. Stores in database and pushes via WebSocket.
    
    Input:
    - user_id (int): Target user ID
    - title (string): Notification title
    - message (string): Message content
    - notification_type (string): Type (job_match, interview, application, onboarding)
    - action_url (string, optional): Link to relevant page
    
    Output: JSON with notification_id and delivery status
    
    Use this to notify users about important events, matches, interviews, etc.
    """
    args_schema: Type[BaseModel] = NotificationToolInput
    
    def _run(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        action_url: str = ""
    ) -> str:
        """Send notification."""
        try:
            db: Session = next(get_db())
            
            # Create notification in database
            notification = Notification(
                recipient_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url,
                is_read=False
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send via WebSocket
            notification_data = {
                "id": notification.id,
                "title": title,
                "message": message,
                "type": notification_type,
                "action_url": action_url,
                "created_at": notification.created_at.isoformat()
            }
            
            # Try to send WebSocket notification
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                loop.run_until_complete(manager.send_personal_message(
                    json.dumps(notification_data),
                    user_id
                ))
                ws_sent = True
            except:
                ws_sent = False
            
            result = {
                "notification_id": notification.id,
                "user_id": user_id,
                "title": title,
                "websocket_sent": ws_sent,
                "database_stored": True,
                "success": True
            }
            
            logger.info(f"✅ Notification sent to user {user_id}: {title}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Notification error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
    
    async def _arun(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        action_url: str = ""
    ) -> str:
        """Async implementation."""
        try:
            db: Session = next(get_db())
            
            # Create notification
            notification = Notification(
                recipient_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url,
                is_read=False
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send via WebSocket
            notification_data = {
                "id": notification.id,
                "title": title,
                "message": message,
                "type": notification_type,
                "action_url": action_url,
                "created_at": notification.created_at.isoformat()
            }
            
            await manager.send_personal_message(json.dumps(notification_data), user_id)
            
            result = {
                "notification_id": notification.id,
                "user_id": user_id,
                "websocket_sent": True,
                "database_stored": True,
                "success": True
            }
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Async notification error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
