from typing import TypeVar, Generic, List
from pydantic.generics import GenericModel

T = TypeVar("T")

class PaginatedResponse(GenericModel, Generic[T]):
    total: int
    page: int
    size: int
    data: List[T]