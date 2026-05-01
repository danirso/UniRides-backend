from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.database import get_db
from app.models.user import User
from app.models.ride import Ride, RideStatus
from app.models.ride_request import RideRequest, RequestStatus
from app.schemas.ride_request import RideRequestCreate, RideRequestResponse
from app.api.dependencies import get_current_user
from app.core.exceptions import RideException

router = APIRouter(prefix="/rides", tags=["Solicitação de caronas"])

@router.post("/{ride_id}/requests", response_model=RideRequestResponse, status_code=status.HTTP_201_CREATED)
def solicitar_vaga(
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

    nova_solicitacao = RideRequest(
        ride_id=ride_id,
        passenger_id=current_user.id,
        passenger_origin=f"SRID=4326;POINT({request_in.origin_lng} {request_in.origin_lat})",
        passenger_destination=f"SRID=4326;POINT({request_in.destination_lng} {request_in.destination_lat})",
        status=RequestStatus.PENDING
    )
    
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)
    
    # TODO: Implementar serviço de notificação Push/Email para alertar o motorista
    
    return nova_solicitacao

@router.post("/{ride_id}/requests/{request_id}/cancel", response_model=RideRequestResponse)
def cancelar_solicitacao(
    ride_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    solicitacao = db.query(RideRequest).filter(
        RideRequest.id == request_id, 
        RideRequest.passenger_id == current_user.id
    ).first()
    
    if not solicitacao or solicitacao.status == RequestStatus.CANCELED:
        raise RideException(status_code=404, code="REQUEST_NOT_FOUND", message="Solicitação não encontrada ou já cancelada.")
        
    was_accepted = solicitacao.status == RequestStatus.ACCEPTED
    
    solicitacao.status = RequestStatus.CANCELED
    
    if was_accepted:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        ride.available_seats += 1

    db.commit()
    db.refresh(solicitacao)
    
    # TODO: Notificar motorista da desistência
    
    return solicitacao

@router.post("/{ride_id}/requests/{request_id}/accept", response_model=RideRequestResponse)
def aceitar_solicitacao(
    ride_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Você não tem permissão para gerenciar esta carona.")
        
    solicitacao = db.query(RideRequest).filter(RideRequest.id == request_id, RideRequest.ride_id == ride_id).first()
    if not solicitacao or solicitacao.status != RequestStatus.PENDING:
        raise RideException(status_code=400, code="INVALID_REQUEST_STATUS", message="A solicitação não é válida para aceite.")

    if ride.available_seats <= 0:
        raise RideException(status_code=400, code="RIDE_FULL", message="Não há vagas suficientes na carona.")

    solicitacao.status = RequestStatus.ACCEPTED
    ride.available_seats -= 1
    
    db.commit()
    db.refresh(solicitacao)
    
    # TODO: Notificar passageiro do aceite
    
    return solicitacao

@router.post("/{ride_id}/requests/{request_id}/reject", response_model=RideRequestResponse)
def rejeitar_solicitacao(
    ride_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(status_code=403, code="ACCESS_DENIED", message="Você não tem permissão para gerenciar esta carona.")
        
    solicitacao = db.query(RideRequest).filter(RideRequest.id == request_id, RideRequest.ride_id == ride_id).first()
    if not solicitacao or solicitacao.status != RequestStatus.PENDING:
        raise RideException(status_code=400, code="INVALID_REQUEST_STATUS", message="A solicitação não é válida para rejeição.")

    solicitacao.status = RequestStatus.REJECTED
    
    db.commit()
    db.refresh(solicitacao)
    
    #TODO: Notificar passageiro da rejeição
    
    return solicitacao