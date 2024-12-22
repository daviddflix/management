from typing import Optional, Any, List, Dict, Union
import aioredis
import json
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Union[str, dict, list],
        expire: Optional[int] = None
    ) -> bool:
        """Set a value in Redis with optional expiration in seconds."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {str(e)}")
            return False

    async def incr(self, key: str) -> Optional[int]:
        """Increment a counter in Redis."""
        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {str(e)}")
            return None

    async def set_json(
        self,
        key: str,
        value: Union[Dict, List],
        expire: Optional[int] = None
    ) -> bool:
        """Set a JSON value in Redis."""
        try:
            return await self.set(key, json.dumps(value), expire)
        except Exception as e:
            logger.error(f"Redis set_json error for key {key}: {str(e)}")
            return False

    async def get_json(self, key: str) -> Optional[Union[Dict, List]]:
        """Get a JSON value from Redis."""
        try:
            value = await self.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis get_json error for key {key}: {str(e)}")
            return None

    async def set_many(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set multiple key-value pairs in Redis."""
        try:
            async with self.redis.pipeline() as pipe:
                for key, value in mapping.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    await pipe.set(key, value, ex=expire)
                await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis set_many error: {str(e)}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple values from Redis."""
        try:
            values = await self.redis.mget(keys)
            return dict(zip(keys, values))
        except Exception as e:
            logger.error(f"Redis get_many error: {str(e)}")
            return {}

    async def cache(
        self,
        key: str,
        value: Any,
        expire: timedelta = timedelta(minutes=5)
    ) -> bool:
        """Cache a value with expiration."""
        try:
            return await self.set(key, value, int(expire.total_seconds()))
        except Exception as e:
            logger.error(f"Redis cache error for key {key}: {str(e)}")
            return False

# Create dependency for FastAPI
async def get_redis_service(redis: aioredis.Redis) -> RedisService:
    return RedisService(redis)
