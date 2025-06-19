from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.database.core import load_sql
from src.users.models import UserIn, UserOut
from src.utils.db_error_parser import handle_sql_error
from src.utils.exceptions import AppException
from src.logger import logger
from src.utils.pagination import paginate_raw_query
from src.utils.paginated_response import PaginatedResponse

def create_user(session: Session, data: UserIn) -> UserOut:
    logger.debug(f"Creating user with data: {data}")
    try:
        stmt = text(load_sql("users/create_user.sql"))
        session.execute(stmt, data.dict())
        session.commit()
        last_id = session.execute(text("SELECT LAST_INSERT_ID()"))
        user_id = last_id.scalar()
        logger.info(f"User created with ID: {user_id}")
        return get_user_by_id(session, user_id)
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception("Database error during user creation")
        handle_sql_error(e, entity="User")


def get_all_users(session: Session, page: int, size: int) -> PaginatedResponse[UserOut]:
    logger.debug(f"Getting paginated users - page: {page}, size: {size}")
    try:
        data_sql = load_sql("users/get_all_users.sql")
        count_sql = load_sql("users/count_users.sql")

        paginated = paginate_raw_query(
            session=session,
            data_sql=data_sql,
            count_sql=count_sql,
            model=UserOut,
            page=page,
            size=size
        )

        logger.info(f"Retrieved {len(paginated.data)} users out of {paginated.total}")
        return paginated

    except SQLAlchemyError as e:
        logger.exception("Database error during get_all_users")
        handle_sql_error(e, entity="User")


def get_user_by_id(session: Session, user_id: int) -> UserOut:
    logger.debug(f"Getting user by ID: {user_id}")
    try:
        stmt = text(load_sql("users/get_user_by_id.sql"))
        row = session.execute(stmt, {"user_id": user_id}).first()
        if not row:
            raise AppException(f"User with ID {user_id} not found", 404, safe_to_show=True)
        user = UserOut(**row._mapping)
        logger.info(f"User found: {user.id}")
        return user
    except SQLAlchemyError as e:
        logger.exception("Database error during get_user_by_id")
        handle_sql_error(e, entity="User")


def update_user(session: Session, user_id: int, data: UserIn) -> UserOut:
    logger.debug(f"Updating user ID {user_id} with data: {data}")
    try:
        params = data.dict(); params["user_id"] = user_id
        stmt = text(load_sql("users/update_user.sql"))
        session.execute(stmt, params)
        session.commit()
        logger.info(f"User updated with ID: {user_id}")
        return get_user_by_id(session, user_id)
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception("Database error during update_user")
        handle_sql_error(e, entity="User")


def delete_user(session: Session, user_id: int) -> None:
    logger.debug(f"Deleting user with ID: {user_id}")
    try:
        stmt = text(load_sql("users/delete_user.sql"))
        result = session.execute(stmt, {"user_id": user_id})
        session.commit()
        if result.rowcount == 0:
            raise AppException(f"User with ID {user_id} not found", 404, safe_to_show=True)
        logger.info(f"User deleted: {user_id}")
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception("Database error during delete_user")
        handle_sql_error(e, entity="User")
