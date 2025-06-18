'''
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
'''

import json
import re
import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("malicious-filter")
logging.basicConfig(level=logging.INFO)

malicious_patterns = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"href\s*=\s*['\"]javascript:", re.IGNORECASE),
    re.compile(r"src\s*=\s*['\"]javascript:", re.IGNORECASE),
    re.compile(r"\bon[a-zA-Z]{2,}\s*=", re.IGNORECASE),
    re.compile(r"\bOR\s+1\s*=\s*1\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bUNION\s+SELECT\b", re.IGNORECASE),
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
]

class BlockMaliciousPayloadMiddleware:
    def __init__(self, app: ASGIApp, max_depth: int = 5):
        self.app = app
        self.max_depth = max_depth

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

        def contains_malicious(value, depth=0) -> bool:
            if depth > self.max_depth:
                return False

            if isinstance(value, str):
                return any(pattern.search(value) for pattern in malicious_patterns)
            elif isinstance(value, dict):
                return any(contains_malicious(v, depth + 1) for v in value.values())
            elif isinstance(value, list):
                return any(contains_malicious(i, depth + 1) for i in value)
            return False

        if contains_malicious(data):
            logger.warning("Blocked malicious request to %s", str(request.url))
            response = JSONResponse(
                status_code=400,
                content={"detail": "Request blocked due to suspected malicious content."}
            )
            await response(scope, receive, send)
            return

        async def receive_with_body() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, receive_with_body, send)
