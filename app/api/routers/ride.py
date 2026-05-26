from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast
from geoalchemy2.types import Geography
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.core.exceptions import RideException
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.ride import Ride, RideStatus
from app.schemas.ride import RideCreate, RideResponse, RideUpdate, RideSearchRequest
from app.api.dependencies import get_current_user
from app.services.maps import buscar_detalhes_da_rota, polyline_to_linestring

router = APIRouter(prefix="/rides", tags=["Caronas"])

@router.post("/", response_model=RideResponse, status_code=status.HTTP_201_CREATED)
async def criar_carona(
    ride_in: RideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    vehicle = db.query(Vehicle).filter(
        Vehicle.id == ride_in.vehicle_id,
        Vehicle.owner_id == current_user.id
    ).first()
    
    if not vehicle:
        raise RideException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="INVALID_VEHICLE",
            message="Veículo inválido ou não pertence a você."
        )
    
    if ride_in.available_seats > vehicle.capacity:
        raise RideException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CAPACITY_EXCEEDED",
            message=f"O veículo suporta no máximo {vehicle.capacity} passageiros."
        )

    detalhes_rota = await buscar_detalhes_da_rota(
        ride_in.origin_lat, ride_in.origin_lng,
        ride_in.destination_lat, ride_in.destination_lng
    )

    nova_carona = Ride(
        **ride_in.model_dump(exclude={
            "origin_lat", "origin_lng", 
            "destination_lat", "destination_lng",
            "origin_address", "destination_address"
        }),
        driver_id=current_user.id,
        origin_address=detalhes_rota["origin_address"],
        destination_address=detalhes_rota["destination_address"],
        origin_geom=f"SRID=4326;POINT({detalhes_rota['start_location']['lng']} {detalhes_rota['start_location']['lat']})",
        destination_geom=f"SRID=4326;POINT({detalhes_rota['end_location']['lng']} {detalhes_rota['end_location']['lat']})",
        distance_km=detalhes_rota["distance_km"],
        estimated_duration_mins=detalhes_rota["duration_mins"],
        route_polyline=detalhes_rota["polyline"],
        route_geom=polyline_to_linestring(detalhes_rota["polyline"])
    )
    
    db.add(nova_carona)
    db.commit()
    db.refresh(nova_carona)
    
    return nova_carona

@router.get("/me", response_model=List[RideResponse])
def listar_minhas_caronas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Ride).options(joinedload(Ride.driver)).filter(Ride.driver_id == current_user.id).all()

@router.patch("/{ride_id}", response_model=RideResponse)
def atualizar_carona(
    ride_id: UUID,
    ride_in: RideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(
        Ride.id == ride_id, 
        Ride.driver_id == current_user.id
    ).first()
    
    if not ride:
        raise RideException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RIDE_NOT_FOUND",
            message="Carona não encontrada ou você não é o motorista."
        )

    update_data = ride_in.model_dump(exclude_unset=True)
    
    new_vehicle_id = update_data.get("vehicle_id", ride.vehicle_id)
    new_seats = update_data.get("available_seats", ride.available_seats)
    
    if "vehicle_id" in update_data or "available_seats" in update_data:
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == new_vehicle_id,
            Vehicle.owner_id == current_user.id
        ).first()
        
        if not vehicle:
            raise RideException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INVALID_VEHICLE",
                message="Veículo inválido."
            )
        
        if new_seats > vehicle.capacity:
            raise RideException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="CAPACITY_EXCEEDED",
                message=f"O veículo suporta no máximo {vehicle.capacity} passageiros."
            )

    for key, value in update_data.items():
        setattr(ride, key, value)
    
    db.commit()
    db.refresh(ride)
    return ride

@router.delete("/{ride_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_carona(
    ride_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(
        Ride.id == ride_id, 
        Ride.driver_id == current_user.id
    ).first()
    
    if not ride:
        raise RideException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RIDE_NOT_FOUND",
            message="Carona não encontrada ou você não é o motorista."
        )
    
    db.delete(ride)
    db.commit()
    return

@router.post("/{ride_id}/start", response_model=RideResponse)
def iniciar_carona(
    ride_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RIDE_NOT_FOUND",
            message="Carona não encontrada."
        )
    if ride.status != RideStatus.SCHEDULED:
        raise RideException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_STATUS_TRANSITION",
            message="Apenas caronas agendadas podem ser iniciadas."
        )
    
    ride.status = RideStatus.IN_PROGRESS
    db.commit()
    db.refresh(ride)
    return ride

@router.post("/{ride_id}/complete", response_model=RideResponse)
def finalizar_carona(
    ride_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RIDE_NOT_FOUND",
            message="Carona não encontrada."
        )
    if ride.status != RideStatus.IN_PROGRESS:
        raise RideException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_STATUS_TRANSITION",
            message="Apenas caronas em andamento podem ser concluídas."
        )
    
    ride.status = RideStatus.COMPLETED
    db.commit()
    db.refresh(ride)
    return ride

@router.post("/{ride_id}/cancel", response_model=RideResponse)
def cancelar_carona(
    ride_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.driver_id == current_user.id).first()
    if not ride:
        raise RideException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RIDE_NOT_FOUND",
            message="Carona não encontrada."
        )
    if ride.status not in [RideStatus.SCHEDULED, RideStatus.IN_PROGRESS]:
        raise RideException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_STATUS_TRANSITION",
            message="Esta carona já foi encerrada ou cancelada."
        )
    
    ride.status = RideStatus.CANCELED
    db.commit()
    db.refresh(ride)
    return ride

@router.post("/search", response_model=list[RideResponse])
def buscar_carona(
    search_params: RideSearchRequest,
    db: AsyncSession= Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    origem_pt = func.ST_SetSRID(func.ST_MakePoint(search_params.origin_lng, search_params.origin_lat), 4326)
    destino_pt = func.ST_SetSRID(func.ST_MakePoint(search_params.destination_lng, search_params.destination_lat), 4326)

    query = select(Ride).options(joinedload(Ride.driver)).where(
        Ride.status == RideStatus.SCHEDULED,
        Ride.available_seats > 0,
        Ride.departure_time > datetime.now(timezone.utc),
        Ride.driver_id != current_user.id,
        
        func.ST_DWithin(
            cast(Ride.route_geom, Geography), 
            cast(origem_pt, Geography), 
            Ride.max_detour_meters
        ),
        
        func.ST_DWithin(
            cast(Ride.route_geom, Geography), 
            cast(destino_pt, Geography), 
            Ride.max_detour_meters
        ),
        
        func.ST_LineLocatePoint(Ride.route_geom, origem_pt) < func.ST_LineLocatePoint(Ride.route_geom, destino_pt)
    )

    result = db.execute(query)
    caronas_compativeis = result.scalars().all()
    
    return caronas_compativeis