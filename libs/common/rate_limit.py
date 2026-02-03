"""Rate limiting dependency for FastAPI.

Usage:
    from fastapi import Depends
    from libs.common.rate_limit import RateLimiter

    @router.get("/sensitive-endpoint", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
    async def sensitive_endpoint():
        ...
"""

from fastapi import Request
from libs.common.exceptions import RateLimitError
from libs.common.redis import get_redis
from redis.asyncio import Redis


class RateLimiter:
    """
    Fixed window rate limiter using Redis.
    Limits requests based on client IP.
    """

    def __init__(self, times: int = 10, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        try:
            redis = await get_redis()

            # Use client IP as identifier
            client_ip = request.client.host if request.client else "unknown"

            # Create a unique key for this rate limit rule + client
            key = (
                f"rate_limit:{client_ip}:{request.url.path}:{self.times}:{self.seconds}"
            )

            # Increment request count
            current_count = await redis.incr(key)

            # If first request, set expiration
            if current_count == 1:
                await redis.expire(key, self.seconds)

            # Check limit
            if current_count > self.times:
                ttl = await redis.ttl(key)
                raise RateLimitError(
                    message="Too many requests",
                    retry_after=ttl if ttl > 0 else self.seconds,
                    details={
                        "limit": self.times,
                        "window_seconds": self.seconds,
                        "current_count": current_count,
                    },
                )

        except Exception as e:
            # Fallback (fail open) if Redis is down, unless it's our own RateLimitError
            if isinstance(e, RateLimitError):
                raise e
            # Log error strictly if needed, but don't block request
            pass
