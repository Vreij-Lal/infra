from typing import Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from src.utils.paginated_response import PaginatedResponse
from typing import Optional

T = TypeVar("T", bound=BaseModel)

def paginate_raw_query(
    session: Session,
    data_sql: str,
    count_sql: str,
    model: Type[T],
    page: int,
    size: int,
    params: Optional[dict] = None 
) -> PaginatedResponse[T]:
    offset = (page - 1) * size
    query_params = {**(params or {}), "limit": size, "offset": offset}

    data_rows = session.execute(text(data_sql), query_params).all()
    total = session.execute(text(count_sql), params or {}).scalar()

    items = [model(**row._mapping) for row in data_rows]

    return PaginatedResponse[T](
        total=total,
        page=page,
        size=size,
        data=items
    )