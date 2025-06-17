from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
import os
from dotenv import load_dotenv
from src.database.core import SessionLocal
from src.users.service import (
    create_user, get_all_users,
    get_user_by_id, update_user, delete_user
)
from src.users.models import UserIn, UserOut
from src.utils.response_builder import make_response
from src.utils.response_models import GenericResponse
from src.utils.exceptions import AppException
from slowapi.decorator import limiter
from src.logger import logger

load_dotenv()
IS_DEV = os.getenv("ENV", "dev") == "dev"

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@limiter.limit("5/minute")
@router.post("/", response_model=GenericResponse[UserOut], responses={409: {"description": "Conflict"}})
def api_create_user(data: UserIn, db: Annotated[Session, Depends(get_db)]):
    logger.info("Received request to create user")
    try:
        user = create_user(db, data)
        logger.info(f"User created successfully: {user.id}")
        return JSONResponse(
            status_code=201,
            content=make_response(
                data=user.model_dump(),
                status=201,
                message="User created successfully."
            )
        )
    except AppException as e:
        logger.warning(f"AppException during user creation: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        logger.exception("Unexpected error during user creation")
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@limiter.limit("5/minute")
@router.get("/", response_model=GenericResponse[list[UserOut]])
def api_get_all(db: Annotated[Session, Depends(get_db)]):
    logger.info("Fetching all users")
    try:
        users = get_all_users(db)
        logger.info(f"Fetched {len(users)} users")
        return JSONResponse(
            status_code=200,
            content=make_response(
                data=[user.model_dump() for user in users],
                status=200,
                message="Users fetched successfully."
            )
        )
    except AppException as e:
        logger.warning(f"AppException during get_all_users: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        logger.exception("Unexpected error during get_all_users")
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@limiter.limit("5/minute")
@router.get("/{user_id}", response_model=GenericResponse[UserOut])
def api_get_one(user_id: int, db: Annotated[Session, Depends(get_db)]):
    logger.info(f"Fetching user with ID: {user_id}")
    try:
        user = get_user_by_id(db, user_id)
        logger.info(f"Fetched user: {user.id}")
        return JSONResponse(
            status_code=200,
            content=make_response(
                data=user.model_dump(),
                status=200,
                message="User fetched successfully."
            )
        )
    except AppException as e:
        logger.warning(f"AppException during get_user_by_id: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        logger.exception("Unexpected error during get_user_by_id")
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@limiter.limit("5/minute")
@router.put("/{user_id}", response_model=GenericResponse[UserOut])
def api_update_user(user_id: int, data: UserIn, db: Annotated[Session, Depends(get_db)]):
    logger.info(f"Updating user with ID: {user_id}")
    try:
        user = update_user(db, user_id, data)
        logger.info(f"User updated successfully: {user.id}")
        return JSONResponse(
            status_code=200,
            content=make_response(
                data=user.model_dump(),
                status=200,
                message="User updated successfully."
            )
        )
    except AppException as e:
        logger.warning(f"AppException during update_user: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        logger.exception("Unexpected error during update_user")
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@limiter.limit("5/minute")
@router.delete("/{user_id}", response_model=GenericResponse[None])
def api_delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    logger.info(f"Deleting user with ID: {user_id}")
    try:
        delete_user(db, user_id)
        logger.info(f"User deleted: {user_id}")
        return JSONResponse(
            status_code=200,
            content=make_response(None, 200, "User deleted successfully.")
        )
    except AppException as e:
        logger.warning(f"AppException during delete_user: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        logger.exception("Unexpected error during delete_user")
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )