from pydantic import field_validator
from src.utils.strict_json_model import StrictBaseModel

class UserIn(StrictBaseModel):
    username: str
    email: str
    is_active: bool = True

class UserOut(UserIn):
    id: int
