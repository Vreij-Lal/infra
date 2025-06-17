from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
from src.logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(f"Response: {response.status_code} - Duration: {duration:.4f}s")

        return response
