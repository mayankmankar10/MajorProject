"""
Request-scoped cache using context variables.
Caches data for the duration of a single request, automatically cleared after.
"""
from contextvars import ContextVar
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Request-scoped cache using context variables
# Each async request gets its own isolated cache
_request_cache: ContextVar[Dict[str, Any]] = ContextVar('request_cache', default=None)

def get_request_cache() -> Dict[str, Any]:
    """
    Get the current request's cache dictionary.
    Creates a new cache if one doesn't exist.
    
    Returns:
        Request-scoped cache dictionary
    """
    cache = _request_cache.get()
    if cache is None:
        cache = {}
        _request_cache.set(cache)
    return cache

def set_request_cache_value(key: str, value: Any):
    """
    Set a value in the request cache.
    
    Args:
        key: Cache key
        value: Value to cache
    """
    cache = get_request_cache()
    cache[key] = value
    logger.debug(f"📝 Request cache SET: {key}")

def get_request_cache_value(key: str, default: Any = None) -> Optional[Any]:
    """
    Get a value from the request cache.
    
    Args:
        key: Cache key
        default: Default value if key not found
        
    Returns:
        Cached value or default
    """
    cache = get_request_cache()
    value = cache.get(key, default)
    
    if value is not default:
        logger.debug(f"✅ Request cache HIT: {key}")
    else:
        logger.debug(f"❌ Request cache MISS: {key}")
    
    return value

def clear_request_cache():
    """
    Clear the request cache.
    Should be called at the end of each request.
    """
    cache = _request_cache.get()
    if cache:
        size = len(cache)
        _request_cache.set({})
        logger.debug(f"🗑️  Request cache cleared ({size} entries)")
    else:
        _request_cache.set({})

def request_cache_exists(key: str) -> bool:
    """
    Check if a key exists in the request cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if key exists, False otherwise
    """
    cache = get_request_cache()
    return key in cache

def get_request_cache_stats() -> Dict[str, Any]:
    """
    Get request cache statistics.
    
    Returns:
        Dictionary with cache stats
    """
    cache = get_request_cache()
    return {
        'size': len(cache),
        'keys': list(cache.keys())
    }
