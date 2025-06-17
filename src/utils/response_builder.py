from typing import Any
from src.utils.response_models import GenericResponse

def make_response(data: Any, status: int, message: str) -> dict:
    return GenericResponse(
        status=status,
        message=message,
        data=data
    ).model_dump()