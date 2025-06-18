'''
import bleach
import re
import json
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from src.utils.response_builder import make_response
from src.logger import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                if not body_bytes:
                    return await call_next(request)

                body = json.loads(body_bytes)
                if not self._is_clean(body):
                    logger.warning("🚫 Malicious input detected")
                    return JSONResponse(
                        status_code=HTTP_400_BAD_REQUEST,
                        content=make_response(
                            data=None,
                            status=HTTP_400_BAD_REQUEST,
                            message="Invalid or potentially dangerous input detected."
                        )
                    )
            except Exception as e:
                logger.warning(f"🛑 Failed to inspect input: {e}")
                return JSONResponse(
                    status_code=HTTP_400_BAD_REQUEST,
                    content=make_response(
                        data=None,
                        status=HTTP_400_BAD_REQUEST,
                        message="Malformed request body."
                    )
                )

        return await call_next(request)

    def _is_clean(self, data):
        def contains_dangerous(value):
            if isinstance(value, str):
                # Clean the value using bleach to remove potentially harmful HTML
                stripped = bleach.clean(value, tags=["b", "i", "u", "a", "p", "br"], strip=True)

                # Enhanced SQL Injection pattern (catching more variants)
                sql_keywords = r'\b(select|insert|delete|drop|update|alter|create|exec|union|--|;|or|and|from|exec|grant|waitfor|sleep|group by|1=1|limit)\b'
                if re.search(sql_keywords, stripped, re.IGNORECASE):
                    return True

                # Enhanced XSS prevention: look for <script> tags, event handlers, javascript URLs, and iframe tags
                xss_keywords = (
                    r'<script.*?>.*?</script>|'  # Match <script> tags
                    r'<.*?on\w+=".*?".*?>|'  # Match event handlers (e.g., onerror, onclick, etc.)
                    r'javascript:.*?alert\(|'  # Match javascript URLs (e.g., javascript:alert(1))
                    r'<iframe.*?>.*?</iframe>'  # Match iframe tags
                )
                if re.search(xss_keywords, stripped, re.IGNORECASE):
                    return True

                # Specifically check for javascript in href or src attributes
                if re.search(r'(href|src)="javascript:.*?"', stripped, re.IGNORECASE):
                    return True

            elif isinstance(value, list):
                return any(contains_dangerous(v) for v in value)
            elif isinstance(value, dict):
                return any(contains_dangerous(v) for v in value.values())

            return False

        return not contains_dangerous(data)
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