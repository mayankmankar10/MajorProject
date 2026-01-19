# backend/chat/chat_routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from backend.db.models import User, ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel
from backend.db.sql_db import get_db
from sqlalchemy.orm import Session
from backend.orchestration import get_dispatcher
from backend.cache.redis_client import get_redis_cache
from backend.cache.request_cache import clear_request_cache
import logging
import uuid
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Redis cache for session storage (with in-memory fallback)
redis_cache = get_redis_cache()

# In-memory fallback if Redis unavailable
chat_sessions_memory: Dict[str, List[Dict[str, str]]] = {}

# Session TTL from environment (default: 7 days = 604800 seconds)
# Chat history is also stored in the database for permanent persistence
CHAT_SESSION_TTL = int(os.getenv("CHAT_SESSION_TTL", "604800"))

def get_chat_history(session_id: str, db: Session) -> List[Dict[str, str]]:
    """Get chat history from database with Redis caching."""
    # Try Redis cache first
    if redis_cache.enabled:
        data = redis_cache.get(f"chat:{session_id}")
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode chat history for session {session_id}")
    
    # Fall through to database
    chat_session = db.query(ChatSessionModel).filter(
        ChatSessionModel.session_id == session_id
    ).first()
    
    if not chat_session:
        return []
    
    # Load messages from database
    messages = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == chat_session.id
    ).order_by(ChatMessageModel.created_at.asc()).all()
    
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Cache in Redis for faster access
    if redis_cache.enabled:
        redis_cache.set(f"chat:{session_id}", json.dumps(history), ttl=CHAT_SESSION_TTL)
    
    return history

def save_chat_history(session_id: str, history: List[Dict[str, str]], user_id: int, db: Session):
    """Save chat history to database and Redis cache."""
    # Save to database
    chat_session = db.query(ChatSessionModel).filter(
        ChatSessionModel.session_id == session_id
    ).first()
    
    if not chat_session:
        # Create new session
        chat_session = ChatSessionModel(
            session_id=session_id,
            user_id=user_id,
            title=None,  # Will be set from first user message
            is_active=True
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
    
    # Get existing message count
    existing_count = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == chat_session.id
    ).count()
    
    # Only add new messages (history contains all messages, but we only want to add the new ones)
    new_messages = history[existing_count:]
    
    for msg_data in new_messages:
        msg = ChatMessageModel(
            session_id=chat_session.id,
            role=msg_data["role"],
            content=msg_data["content"]
        )
        db.add(msg)
    
    # Update session's last_message_at
    chat_session.last_message_at = datetime.utcnow()
    
    # Auto-generate title from first user message if not set
    if not chat_session.title and len(history) > 0:
        first_user_msg = next((m for m in history if m["role"] == "user"), None)
        if first_user_msg:
            # Use first 50 chars of first message as title
            chat_session.title = first_user_msg["content"][:50] + ("..." if len(first_user_msg["content"]) > 50 else "")
    
    db.commit()
    
    # Cache in Redis for faster access
    if redis_cache.enabled:
        redis_cache.set(f"chat:{session_id}", json.dumps(history), ttl=CHAT_SESSION_TTL)
    else:
        chat_sessions_memory[session_id] = history


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: int
    role: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    intermediate_steps: Optional[List] = []

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    chat_msg: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    The orchestrator will determine which tools to use based on user intent.
    """
    try:
        # Clear request cache at start of request
        clear_request_cache()
        
        # Get or create session ID
        session_id = chat_msg.session_id or str(uuid.uuid4())
        
        # Get chat history from database (with Redis cache)
        chat_history = get_chat_history(session_id, db)
        
        # Get dispatcher
        dispatcher = get_dispatcher()
        
        # Dispatch to appropriate orchestrator based on user role
        result = await dispatcher.dispatch(
            user_input=chat_msg.message,
            user_role=chat_msg.role,
            user_id=chat_msg.user_id,  # Pass user_id to orchestrator
            session_id=session_id,
            chat_history=chat_history
        )
        
        # Update chat history
        chat_history.append({
            "role": "user",
            "content": chat_msg.message
        })
        chat_history.append({
            "role": "assistant",
            "content": result.get("output", "")
        })
        
        # Keep only last 20 messages
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        # Save updated history to database
        save_chat_history(session_id, chat_history, chat_msg.user_id, db)
        
        # Store user_id mapping for this session (for backward compatibility with Redis-only mode)
        if redis_cache.enabled:
            redis_cache.set(f"chat_user:{session_id}", str(chat_msg.user_id), ttl=CHAT_SESSION_TTL)
        else:
            chat_sessions_memory[f"user:{session_id}"] = chat_msg.user_id
        
        logger.info(f"Chat message processed for user {chat_msg.user_id}, session {session_id}")
        
        return ChatResponse(
            response=result.get("output", ""),
            session_id=session_id,
            success=result.get("success", True),
            intermediate_steps=result.get("intermediate_steps", [])
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
    finally:
        # Ensure request cache is cleared
        clear_request_cache()

@router.get("/history/{session_id}")
async def get_session_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat history for a session."""
    chat_history = get_chat_history(session_id, db)
    
    return {
        "session_id": session_id,
        "messages": chat_history,
        "total": len(chat_history)
    }

@router.post("/clear/{session_id}")
async def clear_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Clear chat history for a session."""
    # Delete from database
    chat_session = db.query(ChatSessionModel).filter(
        ChatSessionModel.session_id == session_id
    ).first()
    
    if chat_session:
        db.delete(chat_session)
        db.commit()
    
    # Clear from cache
    if redis_cache.enabled:
        redis_cache.delete(f"chat:{session_id}")
    else:
        if session_id in chat_sessions_memory:
            del chat_sessions_memory[session_id]
    
    logger.info(f"Cleared chat session {session_id}")
    
    return {
        "message": "Session cleared",
        "session_id": session_id,
        "success": True
    }

@router.get("/sessions")
async def get_user_sessions(user_id: int = None, db: Session = Depends(get_db)):
    """Get all active sessions for a specific user from database."""
    if not user_id:
        return {"sessions": [], "total": 0}
    
    # Query database for user's sessions
    chat_sessions = db.query(ChatSessionModel).filter(
        ChatSessionModel.user_id == user_id,
        ChatSessionModel.is_active == True
    ).order_by(ChatSessionModel.last_message_at.desc()).all()
    
    sessions = [
        {
            "session_id": session.session_id,
            "title": session.title or "New Chat",
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "message_count": len(session.messages) if session.messages else 0
        }
        for session in chat_sessions
    ]
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


