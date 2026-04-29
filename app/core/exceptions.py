from fastapi import HTTPException
from typing import Optional

class BusinessException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, headers: Optional[dict] = None):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
            headers=headers
        )