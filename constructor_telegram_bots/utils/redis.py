from django.core.cache import cache

from redis import Redis

from typing import Any, cast


def get_redis_client(write: bool = True) -> Redis:
    result: Any = cast(Any, cache)._cache.get_client(write)

    if not isinstance(result, Redis):
        raise TypeError(
            f'Expected redis.Redis client instance, got {type(result).__name__} instead.'
        )

    return result
