import time
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 5, period: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.period = period
        self.access_log = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        now = time.time()
        access_times = self.access_log[ip]

        while access_times and now - access_times[0] > self.period:
            access_times.popleft()

        if len(access_times) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a moment."}
            )

        access_times.append(now)
        return await call_next(request)