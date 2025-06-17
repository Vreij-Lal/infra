'''
OLD SERVICE


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated

from src.database.core import SessionLocal
from src.users.service import (
    create_user, get_all_users,
    get_user_by_id, update_user, delete_user
)
from src.users.models import UserIn, UserOut
from src.utils.response_builder import make_response
from src.utils.response_models import GenericResponse

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=GenericResponse[UserOut])
def api_create_user(data: UserIn, db: Annotated[Session, Depends(get_db)]):
    user = create_user(db, data)
    return JSONResponse(
        status_code=201,
        content=make_response(
            data=user.model_dump(),
            status=201,
            message="User created successfully."
        )
    )


@router.get("/", response_model=GenericResponse[list[UserOut]])
def api_get_all(db: Annotated[Session, Depends(get_db)]):
    users = get_all_users(db)
    return JSONResponse(
        status_code=200,
        content=make_response(
            data=[user.model_dump() for user in users],
            status=200,
            message="Users fetched successfully."
        )
    )


@router.get("/{user_id}", response_model=GenericResponse[UserOut])
def api_get_one(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, detail="Not found")
    return JSONResponse(
        status_code=200,
        content=make_response(
            data=user.model_dump(),
            status=200,
            message="User fetched successfully."
        )
    )


@router.put("/{user_id}", response_model=GenericResponse[UserOut])
def api_update_user(user_id: int, data: UserIn, db: Annotated[Session, Depends(get_db)]):
    user = update_user(db, user_id, data)
    if not user:
        raise HTTPException(404, detail="Not found")
    return JSONResponse(
        status_code=200,
        content=make_response(
            data=user.model_dump(),
            status=200,
            message="User updated successfully."
        )
    )


@router.delete("/{user_id}", response_model=GenericResponse[None])
def api_delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(404, detail="Not found")
    return JSONResponse(
        status_code=200,
        content=make_response(
            data=None,
            status=200,
            message="User deleted successfully."
        )
    )
'''

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
import traceback
import os
from dotenv import load_dotenv

load_dotenv()
IS_DEV = os.getenv("ENV", "dev") == "dev"

from src.database.core import SessionLocal
from src.users.service import (
    create_user, get_all_users,
    get_user_by_id, update_user, delete_user
)
from src.users.models import UserIn, UserOut
from src.utils.response_builder import make_response
from src.utils.response_models import GenericResponse
from src.utils.exceptions import AppException

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=GenericResponse[UserOut], responses={409: {"description": "Conflict"}})
def api_create_user(data: UserIn, db: Annotated[Session, Depends(get_db)]):
    try:
        user = create_user(db, data)
        return JSONResponse(
            status_code=201,
            content=make_response(
                data=user.model_dump(),
                status=201,
                message="User created successfully."
            )
        )
    except AppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@router.get("/", response_model=GenericResponse[list[UserOut]])
def api_get_all(db: Annotated[Session, Depends(get_db)]):
    try:
        users = get_all_users(db)
        return JSONResponse(
            status_code=200,
            content=make_response(
                data=[user.model_dump() for user in users],
                status=200,
                message="Users fetched successfully."
            )
        )
    except AppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@router.get("/{user_id}", response_model=GenericResponse[UserOut])
def api_get_one(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        user = get_user_by_id(db, user_id)
        return JSONResponse(
            status_code=200,
            content=make_response(
                data=user.model_dump(),
                status=200,
                message="User fetched successfully."
            )
        )
    except AppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@router.put("/{user_id}", response_model=GenericResponse[UserOut])
def api_update_user(user_id: int, data: UserIn, db: Annotated[Session, Depends(get_db)]):
    try:
        user = update_user(db, user_id, data)
        return JSONResponse(
            status_code=200,
            content=make_response(
                data=user.model_dump(),
                status=200,
                message="User updated successfully."
            )
        )
    except AppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )

@router.delete("/{user_id}", response_model=GenericResponse[None])
def api_delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        delete_user(db, user_id)
        return JSONResponse(
            status_code=200,
            content=make_response(None, 200, "User deleted successfully.")
        )
    except AppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=make_response(None, e.status_code, e.message)
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content=make_response(None, 500, str(e) if IS_DEV else "Internal server error")
        )