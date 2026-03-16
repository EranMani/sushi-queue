import redis

from app.core.config import settings

"""
THE KITCHEN'S PRIVATE WHITEBOARD (Synchronous Redis Connection)
------------------------------------------------------------------
- Create a synchronous Redis connection for the background workers.
"""

# The single, shared marker the whole kitchen will use.
_redis: redis.Redis | None = None


def get_sync_redis() -> redis.Redis:
    global _redis

    # THE SINGLETON PATTERN
    # Dont need to buy a brand new marker every single time a Chef needs to write a sticky note!
    if _redis is None:
        # from_url: Takes the address and automatically builds the connection tool.
        # decode_responses=True: Translates raw computer bytes into readable Python strings
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis