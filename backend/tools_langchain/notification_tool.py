# backend/tools_langchain/notification_tool.py
from langchain.tools import BaseTool
from typing import Type, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Notification, User, Employee, Employer
from backend.notifications.connection_manager import manager
import json
import logging

logger = logging.getLogger(__name__)


def resolve_to_user_id(db: Session, provided_id: int) -> int:
    """
    INTELLIGENT ID RESOLUTION - Auto-detects and resolves any ID to correct user_id.
    
    This prevents the common bug where application_id (6) or employee_id (53) 
    is mistakenly used instead of user_id (255).
    
    Resolution order:
    1. Check if it's already a valid user_id
    2. Check if it's an employee_id and resolve to user_id
    3. Check if it's an employer_id and resolve to user_id
    4. Return original if nothing matches (let database FK catch it)
    """
    # Step 1: Check if already a valid user_id
    user = db.query(User).filter(User.id == provided_id).first()
    if user:
        logger.debug(f"ID {provided_id} is already a valid user_id")
        return provided_id
    
    # Step 2: Check if it's an employee_id
    employee = db.query(Employee).filter(Employee.id == provided_id).first()
    if employee:
        logger.warning(
            f"⚠️ ID CORRECTION: Received employee_id={provided_id}, "
            f"auto-resolved to user_id={employee.user_id} ({employee.full_name})"
        )
        return employee.user_id
    
    # Step 3: Check if it's an employer_id
    employer = db.query(Employer).filter(Employer.id == provided_id).first()
    if employer:
        logger.warning(
            f"⚠️ ID CORRECTION: Received employer_id={provided_id}, "
            f"auto-resolved to user_id={employer.user_id} ({employer.company_name})"
        )
        return employer.user_id
    
    # Step 4: ID not found anywhere - log error but return anyway
    # The database FK constraint will catch this
    logger.error(
        f"❌ ID {provided_id} not found in users, employees, or employers tables! "
        f"This notification will likely fail."
    )
    return provided_id

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

    llm: Any = Field(default=None, exclude=True)

    

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
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
            
            # INTELLIGENT ID RESOLUTION - Auto-correct wrong IDs
            resolved_user_id = resolve_to_user_id(db, user_id)
            if resolved_user_id != user_id:
                logger.info(f"Resolved provided ID {user_id} to user_id {resolved_user_id}")
            
            # Create notification in database with RESOLVED user_id
            notification = Notification(
                recipient_id=resolved_user_id,  # Use resolved ID!
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
            
            # INTELLIGENT ID RESOLUTION - Auto-correct wrong IDs
            resolved_user_id = resolve_to_user_id(db, user_id)
            if resolved_user_id != user_id:
                logger.info(f"Resolved provided ID {user_id} to user_id {resolved_user_id}")
            
            # Create notification with RESOLVED user_id
            notification = Notification(
                recipient_id=resolved_user_id,  # Use resolved ID!
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url,
                is_read=False
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send via WebSocket with RESOLVED user_id
            notification_data = {
                "id": notification.id,
                "title": title,
                "message": message,
                "type": notification_type,
                "action_url": action_url,
                "created_at": notification.created_at.isoformat()
            }
            
            await manager.send_personal_message(json.dumps(notification_data), resolved_user_id)
            
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
