"""
Cache utility module with thread-safe operations
"""
from datetime import datetime, timedelta, timezone
import threading


class ThreadSafeCache:
    """Thread-safe cache implementation with TTL support"""
    
    def __init__(self, ttl=30):
        """
        Initialize cache
        
        Args:
            ttl: Time to live in seconds (default: 30)
        """
        self.cache = {}
        self.ttl = ttl
        self.lock = threading.Lock()
    
    def get(self, key):
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if datetime.now(timezone.utc) < expiry:
                    return value
                else:
                    # Remove expired entry
                    del self.cache[key]
        return None
    
    def set(self, key, value):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            expiry = datetime.now(timezone.utc) + timedelta(seconds=self.ttl)
            self.cache[key] = (value, expiry)
    
    def invalidate(self, key=None):
        """
        Invalidate cache entry or entire cache
        
        Args:
            key: Cache key to invalidate (None to clear entire cache)
        """
        with self.lock:
            if key is None:
                self.cache.clear()
            elif key in self.cache:
                del self.cache[key]
    
    def get_stats(self):
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            total_entries = len(self.cache)
            expired_entries = 0
            now = datetime.now(timezone.utc)
            
            for key, (value, expiry) in list(self.cache.items()):
                if now >= expiry:
                    expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'ttl': self.ttl
            }


# Global cache instances
batches_cache = ThreadSafeCache(ttl=30)
smb_cache = ThreadSafeCache(ttl=30)
