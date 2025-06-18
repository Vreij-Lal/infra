import time
from collections import defaultdict, deque
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse
from starlette.requests import Request


class RateLimiterMiddleware:
    def __init__(self, app: ASGIApp, max_requests: int = 5, period: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.period = period
        self.access_log = defaultdict(deque)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        ip = request.client.host
        now = time.time()
        access_times = self.access_log[ip]

        # Clear old timestamps
        while access_times and now - access_times[0] > self.period:
            access_times.popleft()

        if len(access_times) >= self.max_requests:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a moment."}
            )
            await response(scope, receive, send)
            return

        access_times.append(now)
        await self.app(scope, receive, send)
