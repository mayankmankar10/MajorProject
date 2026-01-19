# backend/cache/__init__.py
"""
Production caching system with multiple layers:
- Redis for distributed caching (with fallback)
- Tool cache for LRU caching
- Request cache for request-scoped operations
"""

from backend.cache.redis_client import RedisCache
from backend.cache.tool_cache import ToolCache, tool_cache
from backend.cache.request_cache import (
    get_request_cache,
    set_request_cache_value,
    get_request_cache_value,
    clear_request_cache
)

__all__ = [
    'RedisCache',
    'ToolCache',
    'tool_cache',
    'get_request_cache',
    'set_request_cache_value',
    'get_request_cache_value',
    'clear_request_cache'
]
