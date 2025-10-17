"""
In-memory caching system for improved performance
"""
import time
import asyncio
from typing import Any, Dict, Optional, Callable
from functools import wraps
import hashlib
import json
import logging
from inspect import iscoroutinefunction

logger = logging.getLogger(__name__)

class CacheManager:
    """Enhanced in-memory cache with TTL support, statistics, and cleanup"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self._last_cleanup = time.time()
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key"""
        # Create a hash of function name and arguments
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        # Periodic cleanup of expired entries
        if time.time() - self._last_cleanup > 300:  # Every 5 minutes
            self._cleanup_expired()
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires']:
                self.hits += 1
                logger.debug(f"Cache hit for key: {key[:8]}...")
                return entry['value']
            else:
                # Expired, remove from cache
                del self.cache[key]
                self.misses += 1
                logger.debug(f"Cache expired for key: {key[:8]}...")
        else:
            self.misses += 1
        return None
    
    def _cleanup_expired(self) -> int:
        """Remove expired entries from cache"""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if now >= v['expires']]
        for key in expired_keys:
            del self.cache[key]
        self._last_cleanup = now
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl,
            'created': time.time()
        }
        logger.debug(f"Cache set for key: {key[:8]}... (TTL: {ttl}s)")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = time.time()
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if now >= entry['expires'])
        hit_rate = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'memory_usage_estimate': sum(len(str(entry)) for entry in self.cache.values()),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2%}",
            'total_requests': self.hits + self.misses
        }

# Global cache instance
cache_manager = CacheManager()

def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results (supports both sync and async functions)
    
    Args:
        ttl: Time to live in seconds (default: 300)
        key_func: Custom function to generate cache key
    """
    def decorator(func):
        # Check if the function is async
        is_async = iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Only cache successful results (not exceptions)
                if result is not None:
                    cache_manager.set(cache_key, result, ttl)
                    logger.debug(f"Async function {func.__name__} executed in {execution_time:.3f}s and cached")
                
                return result
            
            # Add cache control methods to the decorated function
            async_wrapper.cache_clear = lambda: cache_manager.clear()
            async_wrapper.cache_stats = lambda: cache_manager.stats()
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Only cache successful results (not exceptions)
                if result is not None:
                    cache_manager.set(cache_key, result, ttl)
                    logger.debug(f"Function {func.__name__} executed in {execution_time:.3f}s and cached")
                
                return result
            
            # Add cache control methods to the decorated function
            sync_wrapper.cache_clear = lambda: cache_manager.clear()
            sync_wrapper.cache_stats = lambda: cache_manager.stats()
            
            return sync_wrapper
    return decorator

def cache_key_for_file_list(path: str = "", sort_by: str = "name", sort_order: str = "asc") -> str:
    """Generate cache key for file listing"""
    return f"file_list:{path}:{sort_by}:{sort_order}"

def cache_key_for_session(session_id: str, operation: str) -> str:
    """Generate cache key for session operations"""
    return f"session:{session_id}:{operation}"

def cache_key_for_vector_store(folder_path: str) -> str:
    """Generate cache key for vector store operations"""
    return f"vector_store:{hashlib.md5(folder_path.encode()).hexdigest()}"