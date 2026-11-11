import os
import time
import math
from collections import defaultdict, deque
from fastapi import HTTPException, Request


def authenticate(request: Request) -> None:
    expected = os.getenv("API_TOKEN", "")
    if not expected:
        return
    supplied = request.headers.get("Authorization", "")
    if supplied != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="unauthorized")


class RateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        events = self.events[key]
        while events and events[0] <= now - self.window_seconds:
            events.popleft()
        if len(events) >= self.limit:
            retry_after = max(1, math.ceil(events[0] + self.window_seconds - now))
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        events.append(now)


def authorized_level(request: Request) -> str:
    """Map authenticated caller to configured clearance; never trust body claims."""
    if os.getenv("API_TOKEN"):
        authenticate(request)
        return os.getenv("API_CALLER_ACCESS_LEVEL", "public")
    # Anonymous local development callers are always public.
    return "public"
