'''
import os
import time
from fastapi import FastAPI, Request
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from src.users.router import router as user_router
from src.utils.response_builder import make_response
from src.middlewares.sanitization import BlockMaliciousPayloadMiddleware
from src.extensions.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from src.middlewares.logging import LoggingMiddleware
from src.logger import logger
from src.database.core import engine
from src.sql.migrations.migrations import users, audit_logs
import os


os.makedirs("logs", exist_ok=True) 
app = FastAPI()


app.add_middleware(BlockMaliciousPayloadMiddleware)


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)              

app.state.limiter = limiter

app.include_router(user_router)

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.warning(f"Validation Error on {request.url}: {errors}")
    first_msg = errors[0].get("msg", "Validation error.") if errors else "Validation error."

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=make_response(data=None, status=HTTP_422_UNPROCESSABLE_ENTITY, message=first_msg)
    )

@app.get("/healthcheck")
def root():
    logger.info("Healthcheck endpoint hit")
    return {"message": "I AM ALIVE"}

@app.on_event("startup")
async def initialize_database():
    max_retries = 10
    delay = 3

    for attempt in range(max_retries):
        try:
            with engine.begin() as conn:
                conn.execute(text(users))
                conn.execute(text(audit_logs))
            logger.info("✅ Database tables initialized successfully")
            return
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(f"⏳ Attempt {attempt + 1}/{max_retries} - DB not ready: {e}")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    logger.error("❌ Failed to initialize database after multiple retries")
    raise RuntimeError("Database init failed")



# Rate-limit exceeded exception handler (customized)
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded for {request.url}")
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."}
    )
'''

import os
import time
from fastapi import FastAPI, Request
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from src.users.router import router as user_router
from src.utils.response_builder import make_response
from src.middlewares.sanitization import BlockMaliciousPayloadMiddleware
from src.middlewares.logging import LoggingMiddleware
from src.logger import logger
from src.database.core import engine
from src.sql.migrations.migrations import users, audit_logs
import os

os.makedirs("logs", exist_ok=True) 
app = FastAPI()

app.add_middleware(BlockMaliciousPayloadMiddleware)
app.add_middleware(LoggingMiddleware)              

app.include_router(user_router)

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.warning(f"Validation Error on {request.url}: {errors}")
    first_msg = errors[0].get("msg", "Validation error.") if errors else "Validation error."

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=make_response(data=None, status=HTTP_422_UNPROCESSABLE_ENTITY, message=first_msg)
    )

@app.get("/healthcheck")
def root():
    logger.info("Healthcheck endpoint hit")
    return {"message": "I AM ALIVE"}

@app.on_event("startup")
async def initialize_database():
    max_retries = 10
    delay = 3

    for attempt in range(max_retries):
        try:
            with engine.begin() as conn:
                conn.execute(text(users))
                conn.execute(text(audit_logs))
            logger.info("Database tables initialized successfully")
            return
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} - DB not ready: {e}")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    logger.error("Failed to initialize database after multiple retries")
    raise RuntimeError("Database init failed")
