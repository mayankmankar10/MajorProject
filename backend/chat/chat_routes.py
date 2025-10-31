# backend/chat/chat_routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from backend.utils.auth import get_current_user
from backend.db.models import User
from backend.orchestration import get_dispatcher
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# In-memory session storage (in production, use Redis or similar)
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    intermediate_steps: Optional[List] = []

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    chat_msg: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """
    Send a chat message and get AI response.
    The orchestrator will determine which tools to use based on user intent.
    """
    try:
        # Get or create session ID
        session_id = chat_msg.session_id or str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Get chat history
        chat_history = chat_sessions[session_id]
        
        # Get dispatcher
        dispatcher = get_dispatcher()
        
        # Dispatch to appropriate orchestrator based on user role
        result = await dispatcher.dispatch(
            user_input=chat_msg.message,
            user_role=current_user.role.value,
            session_id=session_id,
            chat_history=chat_history
        )
        
        # Update chat history
        chat_sessions[session_id].append({
            "role": "user",
            "content": chat_msg.message
        })
        chat_sessions[session_id].append({
            "role": "assistant",
            "content": result.get("output", "")
        })
        
        # Keep only last 20 messages
        if len(chat_sessions[session_id]) > 20:
            chat_sessions[session_id] = chat_sessions[session_id][-20:]
        
        logger.info(f"Chat message processed for user {current_user.id}, session {session_id}")
        
        return ChatResponse(
            response=result.get("output", ""),
            session_id=session_id,
            success=result.get("success", True),
            intermediate_steps=result.get("intermediate_steps", [])
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a session."""
    if session_id not in chat_sessions:
        return {"session_id": session_id, "messages": []}
    
    return {
        "session_id": session_id,
        "messages": chat_sessions[session_id],
        "total": len(chat_sessions[session_id])
    }

@router.post("/clear/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Clear chat history for a session."""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        logger.info(f"Cleared chat session {session_id} for user {current_user.id}")
    
    return {
        "message": "Session cleared",
        "session_id": session_id,
        "success": True
    }

@router.get("/sessions")
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    """Get all active sessions for current user."""
    # In a real app, filter by user ID stored with session
    return {
        "sessions": list(chat_sessions.keys()),
        "total": len(chat_sessions)
    }
