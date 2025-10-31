# backend/notifications/connection_manager.py
from typing import Dict
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, user_id: int, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: user_id={user_id}")
    
    def disconnect(self, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected: user_id={user_id}")
    
    async def send_personal_message(self, user_id: int, message: dict):
        """Send a message to a specific user if connected."""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message)
                logger.debug(f"Message sent to user {user_id}: {message.get('type')}")
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    def is_connected(self, user_id: int) -> bool:
        """Check if user is currently connected."""
        return user_id in self.active_connections
    
    def get_connected_count(self) -> int:
        """Get count of active connections."""
        return len(self.active_connections)
    
    def get_connected_users(self) -> list:
        """Get list of connected user IDs."""
        return list(self.active_connections.keys())


# Global instance
manager = ConnectionManager()
