"""In-process system metrics (latency, errors) + request-timing middleware.

Distinct from product metrics. AI token/cost/latency detail lives in analytics_events
(logged per LLM call) and, when configured, LangSmith traces.
"""
from __future__ import annotations

import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_MAX = 1000


class _Rolling:
    def __init__(self) -> None:
        self.latencies_ms: deque[float] = deque(maxlen=_MAX)
        self.requests = 0
        self.errors = 0

    def record(self, latency_ms: float, status: int) -> None:
        self.latencies_ms.append(latency_ms)
        self.requests += 1
        if status >= 500:
            self.errors += 1

    def snapshot(self) -> dict:
        lat = sorted(self.latencies_ms)
        p95 = lat[int(len(lat) * 0.95)] if lat else 0.0
        avg = sum(lat) / len(lat) if lat else 0.0
        return {
            "requests": self.requests,
            "errors": self.errors,
            "error_rate": round(self.errors / self.requests, 4) if self.requests else 0.0,
            "api_latency_ms_avg": round(avg, 1),
            "api_latency_ms_p95": round(p95, 1),
        }


METRICS = _Rolling()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            METRICS.record((time.perf_counter() - start) * 1000, status)
