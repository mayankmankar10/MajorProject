"""
LRU cache for tool responses to avoid repeated expensive operations.
Caches tool results in memory with automatic eviction when full.
"""
import hashlib
import json
from typing import Any, Optional, Dict
import logging
import time

logger = logging.getLogger(__name__)

class ToolCache:
    """
    In-memory LRU cache for tool responses.
    
    Features:
    - Automatic key generation from tool name and parameters
    - FIFO eviction when cache is full
    - TTL support for cache entries
    - Cache hit/miss statistics
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize tool cache.
        
        Args:
            max_size: Maximum number of entries (default: 100)
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Statistics
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, tool_name: str, **kwargs) -> str:
        """
        Generate cache key from tool name and parameters.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            MD5 hash of tool name + sorted parameters
        """
        # Sort kwargs for consistent hashing
        key_str = f"{tool_name}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if 'expires_at' not in entry:
            return False
        return time.time() > entry['expires_at']
    
    def _evict_if_needed(self):
        """Evict oldest entry if cache is full."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"Cache evicted oldest entry: {oldest_key}")
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get(self, tool_name: str, **kwargs) -> Optional[Any]:
        """
        Get cached result for tool call.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(tool_name, **kwargs)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if self._is_expired(entry):
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        logger.debug(f"✅ Cache HIT for {tool_name} (hit rate: {self.get_hit_rate():.1%})")
        return entry['result']
    
    def set(self, tool_name: str, result: Any, ttl: Optional[int] = None, **kwargs):
        """
        Cache tool result.
        
        Args:
            tool_name: Name of the tool
            result: Result to cache
            ttl: Time to live in seconds (uses default if None)
            **kwargs: Tool parameters
        """
        # Cleanup expired entries first
        self._cleanup_expired()
        
        # Evict if needed
        self._evict_if_needed()
        
        key = self._generate_key(tool_name, **kwargs)
        ttl = ttl or self.default_ttl
        
        self.cache[key] = {
            'result': result,
            'expires_at': time.time() + ttl,
            'tool_name': tool_name,
            'cached_at': time.time()
        }
        
        logger.debug(f"📦 Cached result for {tool_name} (TTL: {ttl}s)")
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("🗑️  Tool cache cleared")
    
    def clear_tool(self, tool_name: str):
        """
        Clear all cache entries for a specific tool.
        
        Args:
            tool_name: Name of the tool
        """
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if entry.get('tool_name') == tool_name
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        logger.info(f"🗑️  Cleared {len(keys_to_delete)} cache entries for {tool_name}")
    
    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Hit rate as decimal (0.0 to 1.0)
        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.get_hit_rate(),
            'utilization': len(self.cache) / self.max_size if self.max_size > 0 else 0
        }


# Global tool cache instance
tool_cache = ToolCache(max_size=100, default_ttl=300)  # 5 minutes default TTL
