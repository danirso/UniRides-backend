from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    reviewee_id: UUID = Field(..., description="ID do usuário avaliado")
    rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5 estrelas")
    comment: Optional[str] = Field(None, max_length=500, description="Comentário opcional")


class ReviewResponse(BaseModel):
    id: UUID
    ride_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PendingReviewTarget(BaseModel):
    """Usuário que ainda pode ser avaliado pelo current_user nesta carona."""
    user_id: UUID
    name: str
    role: str  # "driver" ou "passenger"

    model_config = ConfigDict(from_attributes=True)