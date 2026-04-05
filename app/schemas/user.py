from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

#Requisição do cadastro
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    can_drive: bool = False

#Resposta do cadastro
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