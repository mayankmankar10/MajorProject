# backend/tools/notification_tool.py
from langchain.tools import BaseTool
from typing import Optional
from pydantic import BaseModel, Field
from backend.db.sql_db import SessionLocal
from backend.db.models import Notification
from backend.notifications.connection_manager import manager
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class NotificationInput(BaseModel):
    """Input schema for NotificationTool."""
    recipient_id: int = Field(description="User ID of notification recipient")
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message content")
    notification_type: str = Field(description="Type: job_match, interview, application, onboarding")
    action_url: Optional[str] = Field(None, description="URL to link to relevant page")
    metadata: Optional[dict] = Field(None, description="Additional context data")


class NotificationTool(BaseTool):
    """Tool for sending in-app notifications via WebSocket and storing in database."""
    
    name: str = "send_notification"
    description: str = """
    Send an in-app notification to a user. Use this tool to notify users about:
    - Job matches for employees
    - New applications for employers
    - Interview invitations
    - Onboarding tasks
    - Status updates
    
    The notification will be sent via WebSocket if user is online, and stored in database for later retrieval.
    """
    args_schema: type[BaseModel] = NotificationInput
    
    def _run(
        self,
        recipient_id: int,
        title: str,
        message: str,
        notification_type: str,
        action_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Send notification to user."""
        db = SessionLocal()
        try:
            # Create notification in database
            notification = Notification(
                recipient_id=recipient_id,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url,
                metadata=metadata,
                is_read=False
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Try to send via WebSocket if user is connected
            websocket_sent = False
            if manager.is_connected(recipient_id):
                try:
                    # Run async send in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    websocket_sent = loop.run_until_complete(
                        manager.send_personal_message(
                            recipient_id,
                            {
                                "type": "notification",
                                "id": notification.id,
                                "title": title,
                                "message": message,
                                "notification_type": notification_type,
                                "action_url": action_url,
                                "created_at": notification.created_at.isoformat()
                            }
                        )
                    )
                    loop.close()
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
            
            logger.info(f"Notification created: {notification.id} for user {recipient_id}")
            
            return {
                "status": "success",
                "notification_id": notification.id,
                "recipient_id": recipient_id,
                "websocket_sent": websocket_sent,
                "message": f"Notification sent to user {recipient_id}"
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Notification error: {e}")
            return {
                "status": "error",
                "message": f"Failed to send notification: {str(e)}"
            }
        finally:
            db.close()
    
    async def _arun(self, *args, **kwargs):
        """Async version - calls sync implementation."""
        return self._run(*args, **kwargs)
