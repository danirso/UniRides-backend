from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.user import User
from app.models.ride import Ride, RideStatus
from app.models.ride_request import RideRequest, RequestStatus
from app.schemas.ride_request import RideRequestCreate, RideRequestResponse
from app.api.dependencies import get_current_user
from app.core.exceptions import RideException
from app.schemas.ride_request import RideRequestWithPassenger, RideRequestWithRide

router = APIRouter(prefix="/rides", tags=["Ride requests"])

@router.post(
    '/{ride_id}/requests',
    response_model=RideRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Request a seat',
    description=(
        'Request a seat on a scheduled ride. A driver cannot request their own ride, and '
        'duplicate active requests are rejected.'
    ),
)
def request_seat(
    ride_id: UUID,
    request_in: RideRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise RideException(status_code=404, code="RIDE_NOT_FOUND", message="Carona não encontrada.")

    if ride.driver_id == current_user.id:
        raise RideException(status_code=400, code="INVALID_PASSENGER", message="O motorista não pode solicitar vaga na própria carona.")

    if ride.status != RideStatus.SCHEDULED or ride.available_seats <= 0:
        raise RideException(
            status_code=400,
            code="RIDE_UNAVAILABLE",
            message="Esta carona já foi iniciada, cancelada ou não possui vagas disponíveis."
        )

    existing_request = db.query(RideRequest).filter(
        RideRequest.ride_id == ride_id,
        RideRequest.passenger_id == current_user.id,
        RideRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
    ).first()

    if existing_request:
        raise RideException(
            status_code=400,
            code="DUPLICATE_REQUEST",
            message="Você já possui uma solicitação ativa para esta carona."
        )

    new_request = RideRequest(
        ride_id=ride_id,
        passenger_id=current_user.id,
        passenger_origin=f"SRID=4326;POINT({request_in.origin_lng} {request_in.origin_lat})",
        passenger_destination=f"SRID=4326;POINT({request_in.destination_lng} {request_in.destination_lat})",
        origin_address=request_in.origin_address,
        destination_address=request_in.destination_address,
        status=RequestStatus.PENDING
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    # TODO: Notify the driver through push or email.

    return new_request

@router.post(
    '/{ride_id}/requests/{request_id}/cancel',
    response_model=RideRequestResponse,
    summary='Cancel my seat request',
    description=(
        'Cancel a request belonging to the authenticated passenger and the ride in the URL. An '
        'accepted request returns one seat to that ride.'
    ),
)
def cancel_ride_request(
    ride_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride_request_record = db.query(RideRequest).filter(
        RideRequest.id == request_id,
        RideRequest.ride_id == ride_id,
        RideRequest.passenger_id == current_user.id
    ).first()

    if not ride_request_record or ride_request_record.status == RequestStatus.CANCELED:
        raise RideException(status_code=404, code="REQUEST_NOT_FOUND", message="Solicitação não encontrada ou já cancelada.")

    was_accepted = ride_request_record.status == RequestStatus.ACCEPTED

    ride_request_record.status = RequestStatus.CANCELED

    if was_accepted:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        ride.available_seats += 1

    db.commit()
    db.refresh(ride_request_record)

    # TODO: Notify the driver about the cancellation.

    return ride_request_record

@router.post(
    '/{ride_id}/requests/{request_id}/accept',
    response_model=RideRequestResponse,
    summary='Accept a seat request',
    description=(
        'Accept a pending request as the ride driver. Decreases available seats by one; full '
        'rides reject acceptance.'
    ),
)
def accept_ride_request(
    ride_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Você não tem permissão para gerenciar esta carona.")

    ride_request_record = db.query(RideRequest).filter(RideRequest.id == request_id, RideRequest.ride_id == ride_id).first()
    if not ride_request_record or ride_request_record.status != RequestStatus.PENDING:
        raise RideException(status_code=400, code="INVALID_REQUEST_STATUS", message="A solicitação não é válida para aceite.")

    if ride.available_seats <= 0:
        raise RideException(status_code=400, code="RIDE_FULL", message="Não há vagas suficientes na carona.")

    ride_request_record.status = RequestStatus.ACCEPTED
    ride.available_seats -= 1

    db.commit()
    db.refresh(ride_request_record)

    # TODO: Notify the passenger about acceptance.

    return ride_request_record

@router.post(
    '/{ride_id}/requests/{request_id}/reject',
    response_model=RideRequestResponse,
    summary='Reject a seat request',
    description=(
        'Reject a pending request as the ride driver.'
    ),
)
def reject_ride_request(
    ride_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Você não tem permissão para gerenciar esta carona.")

    ride_request_record = db.query(RideRequest).filter(RideRequest.id == request_id, RideRequest.ride_id == ride_id).first()
    if not ride_request_record or ride_request_record.status != RequestStatus.PENDING:
        raise RideException(status_code=400, code="INVALID_REQUEST_STATUS", message="A solicitação não é válida para rejeição.")

    ride_request_record.status = RequestStatus.REJECTED

    db.commit()
    db.refresh(ride_request_record)

    # TODO: Notify the passenger about rejection.

    return ride_request_record

@router.get(
    '/{ride_id}/list-requests',
    response_model=List[RideRequestWithPassenger],
    summary='List requests for my ride',
    description=(
        'Return the requests and passenger details for a ride owned by the authenticated driver.'
    ),
)
def list_ride_requests(
    ride_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise RideException(status_code=404, code="RIDE_NOT_FOUND", message="Carona não encontrada.")

    if ride.driver_id != current_user.id:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Apenas o motorista pode ver as solicitações desta carona.")

    ride_requests = db.query(RideRequest).options(
        joinedload(RideRequest.passenger)
    ).filter(RideRequest.ride_id == ride_id).all()

    return ride_requests

@router.get(
    '/requests/me',
    response_model=List[RideRequestWithRide],
    summary='List my seat requests',
    description=(
        'Return seat requests made by the authenticated passenger, including ride details.'
    ),
)
def list_my_ride_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride_requests = db.query(RideRequest).options(
        joinedload(RideRequest.ride)
    ).filter(RideRequest.passenger_id == current_user.id).all()

    return ride_requests
