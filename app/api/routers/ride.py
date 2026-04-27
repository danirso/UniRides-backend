from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.ride import Ride, RideStatus
from app.schemas.ride import RideCreate, RideResponse,RideUpdate
from app.api.dependencies import get_current_user
from app.services.maps import buscar_detalhes_da_rota

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veículo inválido ou não pertence a você."
        )
    
    if ride_in.available_seats > vehicle.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O veículo suporta no máximo {vehicle.capacity} passageiros."
        )

    detalhes_rota = await buscar_detalhes_da_rota(
        origem=ride_in.origin_address, 
        destino=ride_in.destination_address
    )

    nova_carona = Ride(
        driver_id=current_user.id,
        vehicle_id=ride_in.vehicle_id,
        available_seats=ride_in.available_seats,
        max_detour_meters=ride_in.max_detour_meters,
        departure_time=ride_in.departure_time,
        origin_address=detalhes_rota["origin_address"],
        destination_address=detalhes_rota["destination_address"],
        origin_geom=f"SRID=4326;POINT({detalhes_rota['start_location']['lng']} {detalhes_rota['start_location']['lat']})",
        destination_geom=f"SRID=4326;POINT({detalhes_rota['end_location']['lng']} {detalhes_rota['end_location']['lat']})",
        distance_km=detalhes_rota["distance_km"],
        estimated_duration_mins=detalhes_rota["duration_mins"],
        route_polyline=detalhes_rota["polyline"]
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
    return db.query(Ride).filter(Ride.driver_id == current_user.id).all()

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
        raise HTTPException(status_code=404, detail="Carona não encontrada ou você não é o motorista.")

    update_data = ride_in.model_dump(exclude_unset=True)
    
    new_vehicle_id = update_data.get("vehicle_id", ride.vehicle_id)
    new_seats = update_data.get("available_seats", ride.available_seats)
    
    if "vehicle_id" in update_data or "available_seats" in update_data:
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == new_vehicle_id,
            Vehicle.owner_id == current_user.id
        ).first()
        
        if not vehicle:
            raise HTTPException(status_code=403, detail="Veículo inválido.")
        
        if new_seats > vehicle.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O veículo suporta no máximo {vehicle.capacity} passageiros."
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
        raise HTTPException(status_code=404, detail="Carona não encontrada ou você não é o motorista.")
    
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
        raise HTTPException(status_code=404, detail="Carona não encontrada.")
    if ride.status != RideStatus.SCHEDULED:
        raise HTTPException(status_code=400, detail="Apenas caronas agendadas podem ser iniciadas.")
    
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
        raise HTTPException(status_code=404, detail="Carona não encontrada.")
    if ride.status != RideStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Apenas caronas em andamento podem ser concluídas.")
    
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
        raise HTTPException(status_code=404, detail="Carona não encontrada.")
    if ride.status not in [RideStatus.SCHEDULED, RideStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="Esta carona já foi encerrada ou cancelada.")
    
    ride.status = RideStatus.CANCELED
    db.commit()
    db.refresh(ride)
    return ride