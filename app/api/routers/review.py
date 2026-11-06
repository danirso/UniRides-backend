from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models.user import User
from app.models.ride import Ride, RideStatus
from app.models.ride_request import RideRequest, RequestStatus
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse, PendingReviewTarget, ReviewWithReviewer
from app.api.dependencies import get_current_user
from app.core.exceptions import RideException

router = APIRouter(prefix="/rides", tags=["Reviews"])


def _get_accepted_passenger_ids(db: Session, ride_id: UUID) -> List[UUID]:
    requests = db.query(RideRequest).filter(
        RideRequest.ride_id == ride_id,
        RideRequest.status == RequestStatus.ACCEPTED
    ).all()
    return [r.passenger_id for r in requests]


@router.post(
    '/{ride_id}/reviews',
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Review a ride participant',
    description=(
        'Submit a rating from 1 to 5 after a completed ride. Drivers can review accepted '
        'passengers; passengers can review the driver. Self-reviews and duplicate reviews are '
        'rejected.'
    ),
)
def create_review(
    ride_id: UUID,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise RideException(status_code=404, code="RIDE_NOT_FOUND", message="Carona não encontrada.")

    if ride.status != RideStatus.COMPLETED:
        raise RideException(status_code=400, code="RIDE_NOT_COMPLETED", message="Só é possível avaliar após a conclusão da carona.")

    if review_in.reviewee_id == current_user.id:
        raise RideException(status_code=400, code="INVALID_REVIEWEE", message="Não é possível avaliar a si mesmo.")

    accepted_passenger_ids = _get_accepted_passenger_ids(db, ride_id)
    is_driver = ride.driver_id == current_user.id
    is_passenger = current_user.id in accepted_passenger_ids

    if not is_driver and not is_passenger:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Você não participou desta carona.")

    if is_driver:
        if review_in.reviewee_id not in accepted_passenger_ids:
            raise RideException(status_code=400, code="INVALID_REVIEWEE", message="Só é possível avaliar passageiros que participaram desta carona.")
    else:
        if review_in.reviewee_id != ride.driver_id:
            raise RideException(status_code=400, code="INVALID_REVIEWEE", message="Como passageiro, só é possível avaliar o motorista desta carona.")

    new_review = Review(
        ride_id=ride_id,
        reviewer_id=current_user.id,
        reviewee_id=review_in.reviewee_id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(new_review)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise RideException(status_code=400, code="DUPLICATE_REVIEW", message="Você já avaliou este usuário nesta carona.")

    db.query(User).filter(User.id == review_in.reviewee_id).update(
        {
            "rating_avg": (User.rating_avg * User.rating_count + review_in.rating) / (User.rating_count + 1),
            "rating_count": User.rating_count + 1,
        },
        synchronize_session=False
    )

    db.commit()
    db.refresh(new_review)

    return new_review


@router.get(
    '/{ride_id}/reviews/pending',
    response_model=List[PendingReviewTarget],
    summary='List participants awaiting my review',
    description=(
        'Return the participants the current user can still review after a completed ride.'
    ),
)
def list_pending_reviews(
    ride_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise RideException(status_code=404, code="RIDE_NOT_FOUND", message="Carona não encontrada.")

    if ride.status != RideStatus.COMPLETED:
        return []

    accepted_passenger_ids = _get_accepted_passenger_ids(db, ride_id)
    is_driver = ride.driver_id == current_user.id
    is_passenger = current_user.id in accepted_passenger_ids

    if not is_driver and not is_passenger:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Você não participou desta carona.")

    reviewed_user_ids = {
        r.reviewee_id for r in db.query(Review).filter(
            Review.ride_id == ride_id,
            Review.reviewer_id == current_user.id
        ).all()
    }

    if is_driver:
        target_ids = [pid for pid in accepted_passenger_ids if pid not in reviewed_user_ids]
        role = "passenger"
    else:
        target_ids = [ride.driver_id] if ride.driver_id not in reviewed_user_ids else []
        role = "driver"

    if not target_ids:
        return []

    users = db.query(User).filter(User.id.in_(target_ids)).all()
    return [PendingReviewTarget(user_id=u.id, name=u.name, role=role) for u in users]
