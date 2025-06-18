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

                # Enhanced SQL Injection pattern (more SQL keywords)
                sql_keywords = r'\b(select|insert|delete|drop|update|alter|create|exec|union|--|;|or|and|from)\b'
                if re.search(sql_keywords, stripped, re.IGNORECASE):
                    return True

                # Enhanced XSS prevention: look for <script> tags, JavaScript event handlers, and javascript URLs
                xss_keywords = (
                    r'<script.*?>.*?</script>|'
                    r'<.*?on\w+=".*?".*?>|'
                    r'javascript:.*?alert\(|'
                    r'<iframe.*?>.*?</iframe>'
                )
                if re.search(xss_keywords, stripped, re.IGNORECASE):
                    return True

            elif isinstance(value, list):
                return any(contains_dangerous(v) for v in value)
            elif isinstance(value, dict):
                return any(contains_dangerous(v) for v in value.values())

            return False

        return not contains_dangerous(data)
