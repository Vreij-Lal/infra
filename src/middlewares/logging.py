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

        receive_stream, send_stream = anyio.create_memory_object_stream()

        async def buffered_receive():
            try:
                return await receive_stream.receive()
            except Exception as e:
                logger.error(f"Error in buffered receive: {e}")
                raise

        async def buffer_messages():
            async with send_stream:
                while True:
                    message = await receive()
                    await send_stream.send(message)
                    if message["type"] == "http.request" and not message.get("more_body", False):
                        break

        async with anyio.create_task_group() as tg:
            tg.start_soon(buffer_messages)

            request = Request(scope, buffered_receive)
            logger.info(f"📥 Request received: {request.method} {request.url}")
            start_time = time.time()

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    logger.info(f"📤 Response sent: {message['status']} ({duration:.4f}s)")
                await send(message)

            await self.app(scope, buffered_receive, send_wrapper)
