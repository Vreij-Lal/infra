from fastapi import FastAPI, Request
from sqlalchemy import text
from src.users.router import router as user_router
from src.database.core import engine
from src.sql.migrations.migrations import (users,audit_logs)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from src.utils.response_builder import make_response
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Logs everything: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(user_router)

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_msg = errors[0].get("msg", "Validation error.") if errors else "Validation error."

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=make_response(
            data=None,
            status=HTTP_422_UNPROCESSABLE_ENTITY,
            message=first_msg
        )
    )

@app.on_event("startup")
def apply_migrations():
    with engine.connect() as connection:
        connection.execute(text(users))
        connection.execute(text(audit_logs))

@app.get("/healthcheck")
def root():
    logging.info("Test log from FastAPI")
    return {"message": "I AM ALIVE"}
