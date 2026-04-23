from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    can_drive: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        domain = "@puccampinas.edu.br"
        if not value.endswith(domain):
            raise ValueError("Email inválido, por favor utilize seu email institucional")
        return value.lower()
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    can_drive: Optional[bool] = None

    @field_validator("email")
    @classmethod
    def validate_email_domain_update(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        domain = "@puccampinas.edu.br"
        if not value.endswith(domain):
            raise ValueError("Email inválido, por favor utilize seu email institucional")
        return value.lower()
    
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_email_verified: bool = False
    can_drive: bool
    rating_avg: float
    created_at: datetime

    class Config:
        from_attributes = True