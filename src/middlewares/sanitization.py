from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
import json
import re
import bleach
from src.utils.response_builder import make_response
from src.logger import logger

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
                stripped = bleach.clean(value).strip()
                # Simple blacklist keywords or patterns
                return bool(re.search(r'\b(select|insert|delete|drop|update|or|and)\b|--|<script', stripped, re.IGNORECASE))
            elif isinstance(value, list):
                return any(contains_dangerous(v) for v in value)
            elif isinstance(value, dict):
                return any(contains_dangerous(v) for v in value.values())
            return False

        return not contains_dangerous(data)
