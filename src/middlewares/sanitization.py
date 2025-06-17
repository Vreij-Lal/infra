import json
import re
import bleach
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    sanitized = self._sanitize_data(data)
                    request._body = json.dumps(sanitized).encode("utf-8")
                except Exception:
                    pass 
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
