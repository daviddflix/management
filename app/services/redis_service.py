from typing import Optional, Any, List, Dict, Union
import redis
import json
from datetime import timedelta
from app.core.logging import app_logger as logger

class RedisService:
    def __init__(self, redis: redis.Redis):
        self.redis = redis

    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        try:
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    def set(
        self,
        key: str,
        value: Union[str, dict, list],
        expire: Optional[int] = None
    ) -> bool:
        """Set a value in Redis with optional expiration in seconds."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.redis.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {str(e)}")
            return False

    def incr(self, key: str) -> Optional[int]:
        """Increment a counter in Redis."""
        try:
            return self.redis.incr(key)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {str(e)}")
            return None

    def set_json(
        self,
        key: str,
        value: Union[Dict, List],
        expire: Optional[int] = None
    ) -> bool:
        """Set a JSON value in Redis."""
        try:
            return self.set(key, json.dumps(value), expire)
        except Exception as e:
            logger.error(f"Redis set_json error for key {key}: {str(e)}")
            return False

    def get_json(self, key: str) -> Optional[Union[Dict, List]]:
        """Get a JSON value from Redis."""
        try:
            value = self.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis get_json error for key {key}: {str(e)}")
            return None

    def set_many(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set multiple key-value pairs in Redis."""
        try:
            with self.redis.pipeline() as pipe:
                for key, value in mapping.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    pipe.set(key, value, ex=expire)
                pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis set_many error: {str(e)}")
            return False

    def get_many(self, keys: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple values from Redis."""
        try:
            values = self.redis.mget(keys)
            return dict(zip(keys, values))
        except Exception as e:
            logger.error(f"Redis get_many error: {str(e)}")
            return {}

    def cache(
        self,
        key: str,
        value: Any,
        expire: timedelta = timedelta(minutes=5)
    ) -> bool:
        """Cache a value with expiration."""
        try:
            return self.set(key, value, int(expire.total_seconds()))
        except Exception as e:
            logger.error(f"Redis cache error for key {key}: {str(e)}")
            return False

def get_redis_service(redis_client: redis.Redis) -> RedisService:
    return RedisService(redis_client)
