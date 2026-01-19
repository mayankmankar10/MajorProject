"""
Database Query Result Caching Decorator
Provides caching for expensive database queries to improve performance.
"""
from functools import wraps
from typing import Callable, Any
import json
import hashlib
import logging
from backend.cache.tool_cache import tool_cache

logger = logging.getLogger(__name__)


def cache_query(ttl: int = 600, key_prefix: str = "db_query"):
    """
    Decorator to cache database query results.
    
    Args:
        ttl: Time-to-live in seconds (default: 10 minutes)
        key_prefix: Prefix for cache key (default: "db_query")
    
    Usage:
        @cache_query(ttl=300, key_prefix="job_search")
        def get_active_jobs(location=None, job_type=None):
            # Expensive database query
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            cache_key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": json.dumps(kwargs, sort_keys=True, default=str)
            }
            cache_key_str = f"{key_prefix}:{json.dumps(cache_key_data, sort_keys=True)}"
            cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
            
            # Try to get cached result
            cached_result = tool_cache.get(key_prefix, cache_key=cache_key_hash)
            if cached_result is not None:
                logger.debug(f"⚡ Cache hit for {func.__name__}")
                return json.loads(cached_result) if isinstance(cached_result, str) else cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Cache the result
            try:
                result_json = json.dumps(result, default=str)
                tool_cache.set(
                    key_prefix,
                    result_json,
                    ttl=ttl,
                    cache_key=cache_key_hash
                )
                logger.debug(f"💾 Cached result for {func.__name__} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Failed to cache result for {func.__name__}: {e}")
            
            return result
        
        return wrapper
    return decorator


def cache_async_query(ttl: int = 600, key_prefix: str = "db_query_async"):
    """
    Async version of cache_query decorator.
    
    Args:
        ttl: Time-to-live in seconds (default: 10 minutes)
        key_prefix: Prefix for cache key
    
    Usage:
        @cache_async_query(ttl=300, key_prefix="employee_search")
        async def search_employees(skills=None, experience_min=None):
            # Expensive async database query
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            cache_key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": json.dumps(kwargs, sort_keys=True, default=str)
            }
            cache_key_str = f"{key_prefix}:{json.dumps(cache_key_data, sort_keys=True)}"
            cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
            
            # Try to get cached result
            cached_result = tool_cache.get(key_prefix, cache_key=cache_key_hash)
            if cached_result is not None:
                logger.debug(f"⚡ Cache hit for {func.__name__}")
                return json.loads(cached_result) if isinstance(cached_result, str) else cached_result
            
            # Execute async function and cache result
            result = await func(*args, **kwargs)
            
            # Cache the result
            try:
                result_json = json.dumps(result, default=str)
                tool_cache.set(
                    key_prefix,
                    result_json,
                    ttl=ttl,
                    cache_key=cache_key_hash
                )
                logger.debug(f"💾 Cached result for {func.__name__} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Failed to cache result for {func.__name__}: {e}")
            
            return result
        
        return wrapper
    return decorator
