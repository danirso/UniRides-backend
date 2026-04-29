from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.core.exceptions import VehicleException
from app.models.vehicle import Vehicle
from app.models.user import User
from app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/vehicles", tags=["Veículos"])

@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def registrar_veiculo(vehicle_in: VehicleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.can_drive:
        raise VehicleException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_NOT_DRIVER",
            message="Usuário não cadastrado como motorista."
        )
    
    if db.query(Vehicle).filter(Vehicle.plate == vehicle_in.plate).first():
        raise VehicleException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="PLATE_ALREADY_REGISTERED",
            message="Placa já cadastrada no sistema."
        )

    db_vehicle = Vehicle(**vehicle_in.model_dump(), owner_id=current_user.id)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/", response_model=List[VehicleResponse])
def listar_veiculos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Vehicle).filter(Vehicle.owner_id == current_user.id).all()

@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def atualizar_veiculos(vehicle_id: UUID, vehicle_in: VehicleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.owner_id == current_user.id).first()
    
    if not db_vehicle:
        raise VehicleException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="VEHICLE_NOT_FOUND",
            message="Veículo não encontrado ou acesso negado."
        )
    
    update_data = vehicle_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_vehicle, key, value)
        
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_veiculo(vehicle_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.owner_id == current_user.id).first()
    
    if not db_vehicle:
        raise VehicleException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="VEHICLE_NOT_FOUND",
            message="Veículo não encontrado ou acesso negado."
        )
    
    db.delete(db_vehicle)
    db.commit()