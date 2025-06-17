from typing import Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")

class GenericResponse(GenericModel, Generic[T]):
    status: int
    message: str
    data: T