'''
OLD SERVICE


from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.core import load_sql
from src.users.models import UserIn, UserOut



def create_user(session: Session, data: UserIn) -> UserOut:
    stmt = text(load_sql("users/create_user.sql"))
    session.execute(stmt, data.dict())
    session.commit()
    last_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    user = get_user_by_id(session, last_id)
    return user

def get_all_users(session: Session) -> list[UserOut]:
    stmt = text(load_sql("users/get_all_users.sql"))
    rows = session.execute(stmt).all()
    return [UserOut(**r._mapping) for r in rows]

def get_user_by_id(session: Session, user_id: int) -> UserOut | None:
    stmt = text(load_sql("users/get_user_by_id.sql"))
    row = session.execute(stmt, {"user_id": user_id}).first()
    return UserOut(**row._mapping) if row else None

def update_user(session: Session, user_id: int, data: UserIn) -> UserOut | None:
    params = data.dict(); params["user_id"] = user_id
    stmt = text(load_sql("users/update_user.sql"))
    session.execute(stmt, params)
    session.commit()
    return get_user_by_id(session, user_id)

def delete_user(session: Session, user_id: int) -> bool:
    stmt = text(load_sql("users/delete_user.sql"))
    result = session.execute(stmt, {"user_id": user_id})
    session.commit()
    return result.rowcount > 0
'''

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.database.core import load_sql
from src.users.models import UserIn, UserOut
from src.utils.db_error_parser import handle_sql_error
from src.utils.exceptions import AppException

def create_user(session: Session, data: UserIn) -> UserOut:
    try:
        stmt = text(load_sql("users/create_user.sql"))
        session.execute(stmt, data.dict())
        session.commit()
        last_id = session.execute(text("SELECT LAST_INSERT_ID()"))
        user_id = last_id.scalar()
        return get_user_by_id(session, user_id)
    except SQLAlchemyError as e:
        session.rollback()
        handle_sql_error(e, entity="User")

def get_all_users(session: Session) -> list[UserOut]:
    try:
        stmt = text(load_sql("users/get_all_users.sql"))
        rows = session.execute(stmt).all()
        return [UserOut(**r._mapping) for r in rows]
    except SQLAlchemyError as e:
        handle_sql_error(e, entity="User")

def get_user_by_id(session: Session, user_id: int) -> UserOut:
    try:
        stmt = text(load_sql("users/get_user_by_id.sql"))
        row = session.execute(stmt, {"user_id": user_id}).first()
        if not row:
            raise AppException(f"User with ID {user_id} not found", 404, safe_to_show=True)
        return UserOut(**row._mapping)
    except SQLAlchemyError as e:
        handle_sql_error(e, entity="User")

def update_user(session: Session, user_id: int, data: UserIn) -> UserOut:
    try:
        params = data.dict(); params["user_id"] = user_id
        stmt = text(load_sql("users/update_user.sql"))
        session.execute(stmt, params)
        session.commit()
        return get_user_by_id(session, user_id)
    except SQLAlchemyError as e:
        session.rollback()
        handle_sql_error(e, entity="User")

def delete_user(session: Session, user_id: int) -> None:
    try:
        stmt = text(load_sql("users/delete_user.sql"))
        result = session.execute(stmt, {"user_id": user_id})
        session.commit()
        if result.rowcount == 0:
            raise AppException(f"User with ID {user_id} not found", 404, safe_to_show=True)
    except SQLAlchemyError as e:
        session.rollback()
        handle_sql_error(e, entity="User")
