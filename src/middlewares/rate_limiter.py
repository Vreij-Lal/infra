'''
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
'''



from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

class BlockMaliciousPayloadMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        if request.method not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            await self.app(scope, receive, send)
            return

        body = await request.body()
        if not body:
            await self.app(scope, receive, send)
            return

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            await self.app(scope, receive, send)
            return

        def contains_malicious(value) -> bool:
            if isinstance(value, str):
                for pattern in malicious_patterns:
                    if pattern.search(value):
                        return True
            elif isinstance(value, dict):
                return any(contains_malicious(v) for v in value.values())
            elif isinstance(value, list):
                return any(contains_malicious(i) for i in value)
            return False

        if contains_malicious(data):
            response = JSONResponse(
                status_code=400,
                content={"detail": "Request blocked due to suspected malicious content."}
            )
            await response(scope, receive, send)
            return

        async def receive_with_body():
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, receive_with_body, send)