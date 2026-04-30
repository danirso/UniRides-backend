from fastapi import HTTPException
from typing import Optional

class AppException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, headers: Optional[dict] = None):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
            headers=headers
        )
        
class AuthException(AppException):
    pass

class RideException(AppException):
    pass

class VehicleException(AppException):
    pass

class UserException(AppException):
    pass
