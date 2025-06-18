from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import re, json

malicious_patterns = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"href\s*=\s*['\"]javascript:", re.IGNORECASE),
    re.compile(r"src\s*=\s*['\"]javascript:", re.IGNORECASE),
    re.compile(r"\bon[a-zA-Z]{2,}\s*=", re.IGNORECASE),
    re.compile(r"\bOR\s+1\s*=\s*1\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bUNION\s+SELECT\b", re.IGNORECASE)
]

class BlockMaliciousPayloadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return await call_next(request)
        body_bytes = await request.body()
        if not body_bytes:
            return await call_next(request)
        try:
            body_data = json.loads(body_bytes)
        except json.JSONDecodeError:
            return await call_next(request)
        def contains_malicious(value) -> bool:
            if isinstance(value, str):
                for pattern in malicious_patterns:
                    if pattern.search(value):
                        return True
            elif isinstance(value, dict):
                for val in value.values():
                    if contains_malicious(val):
                        return True
            elif isinstance(value, list):
                for item in value:
                    if contains_malicious(item):
                        return True
            return False

        if contains_malicious(body_data):
            return JSONResponse(
                status_code=400,
                content={"detail": "Request blocked due to suspected malicious content."}
            )
        async def receive_again():
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        request._receive = receive_again

        return await call_next(request)