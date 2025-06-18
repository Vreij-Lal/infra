import json
import re
import bleach
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.logger import logger

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    sanitized = self._sanitize_data(data)
                    new_body = json.dumps(sanitized).encode("utf-8")

                    async def receive():
                        return {"type": "http.request", "body": new_body}

                    request._receive = receive
                    logger.info("🛡 InputSanitizationMiddleware applied to request body")
                    logger.debug(f"Sanitized body: {sanitized}")

                except Exception as e:
                    logger.warning(f"Sanitization failed: {e}")

        return await call_next(request)

    def _sanitize_data(self, data):
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(i) for i in data]
        elif isinstance(data, str):
            value = data.strip()
            value = bleach.clean(value)
            value = re.sub(r'[^\x00-\x7F]+', '', value)
            value = re.sub(r'(--|\b(select|insert|delete|drop|update|or|and)\b)', '', value, flags=re.IGNORECASE)
            return value
        return data
