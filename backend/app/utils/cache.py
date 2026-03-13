"""
Modular cache utility for AccessLens.
Supports both in-memory and Redis backends.
"""
from typing import Any, Optional, Dict
import json
import time
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._redis = None
        self._initialized = False

    async def initialize(self):
        # In-memory is always active as L1
        if settings.redis_url:
            # Check if we need to (re)initialize Redis
            # In testing, loops might change between tests
            reinit = False
            if not self._initialized:
                reinit = True
            elif self._redis and settings.testing:
                # Basic check to see if loop is still valid
                try:
                    await self._redis.ping()
                except Exception:
                    reinit = True
            
            if reinit:
                try:
                    import redis.asyncio as aioredis
                    if self._redis:
                        await self._redis.aclose()
                    self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
                    logger.info("Redis cache initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Redis, falling back to in-memory: {e}")
        
        self._initialized = True

    async def get(self, key: str) -> Optional[Any]:
        # Check local L1 first
        if key in self._local_cache:
            entry = self._local_cache[key]
            if entry["expiry"] > time.time():
                return entry["data"]
            else:
                del self._local_cache[key]

        # Check Redis L2
        if self._redis:
            try:
                val = await self._redis.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
        
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Set local L1
        self._local_cache[key] = {
            "data": value,
            "expiry": time.time() + ttl
        }

        # Set Redis L2
        if self._redis:
            try:
                await self._redis.set(key, json.dumps(value), ex=ttl)
            except Exception as e:
                logger.error(f"Redis set failed: {e}")

    async def clear(self):
        self._local_cache.clear()
        if self._redis:
            await self._redis.flushdb()

cache_manager = CacheManager()
