from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.config import settings


def _is_local_test_email(value: str) -> bool:
    return (
        settings.ENVIRONMENT == "dev"
        and settings.ALLOW_LOCAL_TEST_EMAILS
        and value.rsplit("@", 1)[-1].lower() == "example.com"
    )

class UserCreate(BaseModel):
    name: str = Field(..., description="Display name.")
    email: EmailStr = Field(..., description="University email; example.com is also allowed by the local runner.")
    password: str = Field(..., description="Account password.", json_schema_extra={"writeOnly": True})
    can_drive: bool = False

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "name": "Local Driver", "email": "driver@example.com",
        "password": "LocalDemo123!", "can_drive": True,
    }]})

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        domain = ("@puccampinas.edu.br","@puc-campinas.edu.br","@dac.unicamp.br")
        if not value.endswith(domain) and not _is_local_test_email(value):
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
        if not value.endswith(domain) and not _is_local_test_email(value):
            raise ValueError("Email inválido, por favor utilize seu email institucional")
        return value.lower()

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_email_verified: bool = False
    can_drive: bool
    rating_avg: float
    rating_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
