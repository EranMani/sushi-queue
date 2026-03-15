from redis.asyncio import Redis

from app.core.config import settings

"""
Use Singleton Pattern to ensure that there is only one instance of the Redis client for the entire restaurant.
Start as None because the restaurant hasn't opened yet.
"""
_redis: Redis | None = None


async def get_redis() -> Redis:
    """
    Get the Redis client for the entire restaurant
    Create the connection if it doesn't exist
    """
    global _redis
    
    # Singleton Pattern
    if _redis is None:
        # decode_responses=True: "Read and write in plain Python strings, not raw bytes!"
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
        
    return _redis

async def close_redis() -> None:
    """
    Close the Redis client when the restaurant closes.
    """
    global _redis
    
    # At the end of the day, safely close the connection if exists and put it away.
    if _redis is not None:
        await _redis.aclose()
        _redis = None