from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    reviewee_id: UUID = Field(..., description="ID of the participant being reviewed.")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars.")
    comment: Optional[str] = Field(None, max_length=500, description="Optional review comment.")


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
    """Participant the current user can still review for this ride."""
    user_id: UUID
    name: str
    role: str  # "driver" or "passenger"

    model_config = ConfigDict(from_attributes=True)

class ReviewWithReviewer(BaseModel):
    id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime
    reviewer_name: str

    model_config = ConfigDict(from_attributes=True)
