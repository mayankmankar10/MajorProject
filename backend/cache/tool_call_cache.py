# backend/cache/tool_call_cache.py
"""
Session-level caching for tool calls to prevent redundant execution.
Cache persists for the duration of a chat session and is cleared when sessions end.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ToolCallCache:
    """Cache tool results within a chat session to prevent duplicate calls."""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize tool call cache.
        
        Args:
            ttl_seconds: Time-to-live for cached items (default 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}  # {session_id: {cache_key: {result, timestamp}}}
        self._ttl = ttl_seconds
        logger.info(f"📦 ToolCallCache initialized with TTL={ttl_seconds}s")
    
    def _make_key(self, tool_name: str, **kwargs) -> str:
        """
        Create a cache key from tool name and arguments.
        
        Args:
            tool_name: Name of the tool being called
            **kwargs: Tool arguments
            
        Returns:
            Hashed cache key
        """
        # Sort kwargs to ensure consistent hashing
        sorted_args = json.dumps(kwargs, sort_keys=True)
        key_string = f"{tool_name}::{sorted_args}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, session_id: str, tool_name: str, **kwargs) -> Optional[str]:
        """
        Get cached tool result if available and not expired.
        
        Args:
            session_id: Chat session ID
            tool_name: Name of the tool
            **kwargs: Tool arguments
            
        Returns:
            Cached result or None if not found/expired
        """
        if session_id not in self._cache:
            return None
        
        cache_key = self._make_key(tool_name, **kwargs)
        cached_item = self._cache[session_id].get(cache_key)
        
        if not cached_item:
            return None
        
        # Check expiration
        age = time.time() - cached_item["timestamp"]
        if age > self._ttl:
            logger.info(f"🕒 Cache EXPIRED for {tool_name} (age: {age:.1f}s)")
            del self._cache[session_id][cache_key]
            return None
        
        logger.info(f"✅ Cache HIT for {tool_name} in session {session_id[:8]}... (age: {age:.1f}s)")
        return cached_item["result"]
    
    def set(self, session_id: str, tool_name: str, result: str, **kwargs):
        """
        Cache a tool result for the session.
        
        Args:
            session_id: Chat session ID
            tool_name: Name of the tool
            result: Tool execution result
            **kwargs: Tool arguments
        """
        if session_id not in self._cache:
            self._cache[session_id] = {}
        
        cache_key = self._make_key(tool_name, **kwargs)
        self._cache[session_id][cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
        
        logger.info(f"💾 Cached result for {tool_name} in session {session_id[:8]}...")
    
    def clear_session(self, session_id: str):
        """
        Clear all cached data for a specific session.
        
        Args:
            session_id: Session to clear
        """
        if session_id in self._cache:
            items_cleared = len(self._cache[session_id])
            del self._cache[session_id]
            logger.info(f"🗑️  Cleared {items_cleared} cached items for session {session_id[:8]}...")
    
    def clear_all(self):
        """Clear entire cache (useful for testing)."""
        sessions_cleared = len(self._cache)
        self._cache.clear()
        logger.info(f"🗑️  Cleared cache for {sessions_cleared} sessions")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_sessions = len(self._cache)
        total_items = sum(len(items) for items in self._cache.values())
        
        return {
            "total_sessions": total_sessions,
            "total_cached_items": total_items,
            "ttl_seconds": self._ttl
        }


# Global cache instance
_tool_call_cache = ToolCallCache()


def get_tool_call_cache() -> ToolCallCache:
    """Get the global tool call cache instance."""
    return _tool_call_cache
