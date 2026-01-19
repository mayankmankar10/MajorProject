"""
Redis client with graceful fallback to in-memory storage.
If Redis is unavailable, the system continues to work using in-memory caching.
"""
import redis
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Redis client wrapper with automatic fallback to disabled mode.
    
    Features:
    - Automatic connection testing
    - Graceful degradation if Redis unavailable
    - JSON-compatible string storage
    - Configurable TTL
    """
    
    def __init__(self):
        """Initialize Redis client and test connection."""
        self.client = None
        self.enabled = False
        
        # Check if Redis is enabled in config
        redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        
        if not redis_enabled:
            logger.info("📦 Redis disabled in configuration (REDIS_ENABLED=false)")
            return
        
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info(f"✅ Redis connected: {redis_url}")
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️  Redis unavailable, using in-memory fallback: {e}")
            self.client = None
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Redis initialization error: {e}")
            self.client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/Redis unavailable
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set value in Redis with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (string)
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def get_keys(self, pattern: str) -> list:
        """
        Get all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "chat:*")
            
        Returns:
            List of matching keys
        """
        if not self.enabled or not self.client:
            return []
        
        try:
            keys = self.client.keys(pattern)
            return keys if keys else []
        except Exception as e:
            logger.error(f"Redis GET_KEYS error for pattern '{pattern}': {e}")
            return []
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "chat:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR_PATTERN error for pattern '{pattern}': {e}")
            return 0


# Global Redis instance
_redis_cache: Optional[RedisCache] = None

def get_redis_cache() -> RedisCache:
    """Get or create global Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
