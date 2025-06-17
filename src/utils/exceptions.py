'''
OLD IMPLEMENTATION
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
'''

import os

class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str | None = None, safe_to_show: bool = False):
        self._original_message = message
        self.status_code = status_code
        self.code = code

        if safe_to_show or os.getenv("ENV", "dev") == "dev":
            self.message = message
        else:
            self.message = "An unexpected error occurred."
