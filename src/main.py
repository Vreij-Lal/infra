from fastapi import FastAPI, Request
from sqlalchemy import text
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from src.users.router import router as user_router
from src.utils.response_builder import make_response
from src.middlewares.sanitization import InputSanitizationMiddleware
from src.extensions.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from src.middlewares.logging import LoggingMiddleware
from src.logger import logger

app = FastAPI()

app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(LoggingMiddleware)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

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
