from contextvars import ContextVar
from typing import Optional, Dict, Any, List

# Global context variable to store the current session ID
# This allows tools to access the session ID without it being passed as an argument
current_session_id: ContextVar[Optional[str]] = ContextVar("current_session_id", default=None)

# Simple in-memory session store
# Structure: { session_id: { key: value } }
_session_store: Dict[str, Dict[str, Any]] = {}

def get_session_data(key: str, default: Any = None) -> Any:
    """Get data for the current session."""
    session_id = current_session_id.get()
    if not session_id:
        return default
    
    session_data = _session_store.get(session_id, {})
    return session_data.get(key, default)

def set_session_data(key: str, value: Any):
    """Set data for the current session."""
    session_id = current_session_id.get()
    if not session_id:
        return
    
    if session_id not in _session_store:
        _session_store[session_id] = {}
    
    _session_store[session_id][key] = value

def clear_session_data(session_id: str):
    """Clear data for a session (e.g. on disconnect)."""
    if session_id in _session_store:
        del _session_store[session_id]
