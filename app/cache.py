"""Redis cache configuration and utilities"""
import json
import redis.asyncio as redis
from typing import Optional, Any
from app.config import settings


class CacheService:
    """Redis cache service"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int = settings.cache_ttl
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return False

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return False

    async def clear_all(self) -> bool:
        """Clear all cache"""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False


# Global cache instance
cache = CacheService()


def get_cache_key(prefix: str, *args) -> str:
    """Generate cache key from prefix and arguments"""
    key_parts = [prefix] + [str(arg) for arg in args]
    return ":".join(key_parts)
