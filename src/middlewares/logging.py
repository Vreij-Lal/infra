import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"📥 Request received: {request.method} {request.url}")
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(f"📤 Response sent: {response.status_code} ({duration:.4f}s)")

        return response
