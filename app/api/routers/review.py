from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.ride import Ride, RideStatus
from app.models.ride_request import RideRequest, RequestStatus
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse, PendingReviewTarget
from app.api.dependencies import get_current_user
from app.core.exceptions import RideException

router = APIRouter(prefix="/rides", tags=["Avaliações"])


def _get_accepted_passenger_ids(db: Session, ride_id: UUID) -> List[UUID]:
    requests = db.query(RideRequest).filter(
        RideRequest.ride_id == ride_id,
        RideRequest.status == RequestStatus.ACCEPTED
    ).all()
    return [r.passenger_id for r in requests]


@router.post("/{ride_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def criar_avaliacao(
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

    ja_avaliou = db.query(Review).filter(
        Review.ride_id == ride_id,
        Review.reviewer_id == current_user.id,
        Review.reviewee_id == review_in.reviewee_id
    ).first()

    if ja_avaliou:
        raise RideException(status_code=400, code="DUPLICATE_REVIEW", message="Você já avaliou este usuário nesta carona.")

    nova_avaliacao = Review(
        ride_id=ride_id,
        reviewer_id=current_user.id,
        reviewee_id=review_in.reviewee_id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(nova_avaliacao)

    reviewee = db.query(User).filter(User.id == review_in.reviewee_id).first()
    total_atual = float(reviewee.rating_avg) * reviewee.rating_count
    reviewee.rating_count += 1
    reviewee.rating_avg = round((total_atual + review_in.rating) / reviewee.rating_count, 2)

    db.commit()
    db.refresh(nova_avaliacao)

    return nova_avaliacao


@router.get("/{ride_id}/reviews/pending", response_model=List[PendingReviewTarget])
def listar_avaliacoes_pendentes(
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

    ja_avaliados_ids = {
        r.reviewee_id for r in db.query(Review).filter(
            Review.ride_id == ride_id,
            Review.reviewer_id == current_user.id
        ).all()
    }

    if is_driver:
        alvo_ids = [pid for pid in accepted_passenger_ids if pid not in ja_avaliados_ids]
        role = "passenger"
    else:
        alvo_ids = [ride.driver_id] if ride.driver_id not in ja_avaliados_ids else []
        role = "driver"

    if not alvo_ids:
        return []

    usuarios = db.query(User).filter(User.id.in_(alvo_ids)).all()
    return [PendingReviewTarget(user_id=u.id, name=u.name, role=role) for u in usuarios]