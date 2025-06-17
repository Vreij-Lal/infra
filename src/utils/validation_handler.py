from pydantic import ValidationError
from src.utils.exceptions import AppException

def handle_pydantic_validation_error(e: ValidationError, entity: str = "Payload") -> None:
    errors = e.errors()
    first_error = errors[0] if errors else {}
    message = first_error.get("msg", "Validation error.")
    raise AppException(f"{entity}: {message}", 422, safe_to_show=True)

def safe_model_parse(model_class, data: dict, entity: str):
    try:
        return model_class(**data)
    except ValidationError as e:
        handle_pydantic_validation_error(e, entity)