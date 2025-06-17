from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from src.utils.exceptions import AppException
from pymysql.err import IntegrityError as MySQLIntegrityError

def handle_integrity_error(e: IntegrityError, entity: str = "Record") -> None:
    code = getattr(e.orig, 'args', [None])[0]  # MySQL error code

    if code == 1062:  # Duplicate entry
        raise AppException(f"{entity} already exists.", 409, safe_to_show=True)

    elif code == 1048:  # Column cannot be null
        raise AppException(f"{entity} is missing required fields.", 400, safe_to_show=True)

    elif code == 1452:  # Foreign key constraint fails
        raise AppException(f"{entity} references invalid data.", 400, safe_to_show=True)

    else:
        raise AppException("Database integrity error.", 500)
    
def handle_sql_error(e: SQLAlchemyError, entity: str = "Record") -> None:
    if isinstance(e, IntegrityError):
        handle_integrity_error(e, entity)
    elif isinstance(e, OperationalError):
        code = getattr(e.orig, 'args', [None])[0]
        if code in (2006, 2013):  # MySQL server has gone away / Lost connection
            raise AppException("Database connection issue. Please try again later.", 503, safe_to_show=True)
        raise AppException("Temporary database issue. Please try again later.", 503, safe_to_show=True)
    else:
        raise AppException("Unexpected database error occurred.", 500)
