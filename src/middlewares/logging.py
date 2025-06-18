'''
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response
from src.logger import logger
import time

class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        logger.info(f"📥 Request received: {request.method} {request.url}")
        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                logger.info(f"📤 Response sent: {message['status']} ({duration:.4f}s)")
            await send(message)

        await self.app(scope, receive, send_wrapper)
'''

from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response
from src.logger import logger
import time
import anyio

class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Step 1: Fully buffer the original receive stream
        messages = []
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.request" and not message.get("more_body", False):
                break

        # Step 2: Create a new receive() that replays the buffered messages
        async def buffered_receive():
            if messages:
                return messages.pop(0)
            else:
                await anyio.sleep(3600)  # shouldn't happen
                raise RuntimeError("No more messages to receive")

        request = Request(scope, buffered_receive)
        logger.info(f"📥 Request received: {request.method} {request.url}")
        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                logger.info(f"📤 Response sent: {message['status']} ({duration:.4f}s)")
            await send(message)

        await self.app(scope, buffered_receive, send_wrapper)
