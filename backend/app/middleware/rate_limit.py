"""Basic per-endpoint, per-client rate limiting (in-process token buckets).

Complements the Postgres-backed per-user daily caps (usage_service). This guards
raw request bursts per (client-ip, path); it is intentionally simple — single-host,
pilot scale — and returns a 429 with the standard error envelope.
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# path prefix -> (max requests, window seconds)
_LIMITS: dict[str, tuple[int, int]] = {
    "/interview/answer": (30, 60),
    "/interview/start": (10, 60),
    "/resume/upload": (20, 60),
    "/jd/upload": (20, 60),
    "/auth": (30, 60),
}
_DEFAULT = (120, 60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[tuple[str, str], list[float]] = defaultdict(list)

    def _limit_for(self, path: str) -> tuple[int, int]:
        for prefix, limit in _LIMITS.items():
            if path.startswith(prefix):
                return limit
        return _DEFAULT

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client = request.client.host if request.client else "unknown"
        max_req, window = self._limit_for(path)
        now = time.monotonic()
        key = (client, path)
        bucket = self._hits[key]
        # drop expired
        cutoff = now - window
        self._hits[key] = [t for t in bucket if t > cutoff]
        if len(self._hits[key]) >= max_req:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMITED",
                                    "message": "Too many requests. Please slow down.",
                                    "details": {}}},
            )
        self._hits[key].append(now)
        return await call_next(request)
