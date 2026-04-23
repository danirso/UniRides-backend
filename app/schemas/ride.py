from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from uuid import UUID

class RideBase(BaseModel):
    available_seats: int = Field(..., gt=0, description="Número de assentos disponíveis")
    max_detour_meters: int = Field(0, ge=0, description="Desvio máximo aceitável em metros")
    departure_time: datetime = Field(..., description="Horário de partida")
    start_point: str = Field(..., description="Coordenadas de partida")
    end_point: str = Field(..., description="Coordenadas de chegada")
    # Estimativas (Opcionais na criação, podem ser calculadas depois)
    estimated_duration_mins: Optional[int] = Field(None, ge=0)
    estimated_distance_km: Optional[Decimal] = Field(None, ge=0)
    route_line: Optional[str] = None

class RideCreate(RideBase):
    vehicle_id: UUID = Field(..., description="ID do veículo utilizado na carona")

class RideUpdate(BaseModel):
    available_seats: Optional[int] = Field(None, gt=0)
    max_detour_meters: Optional[int] = Field(None, ge=0)
    departure_time: Optional[datetime] = None
    start_point : Optional[str] = None
    end_point: Optional[str] = None
    vehicle_id: Optional[UUID] = None

class RideResponse(RideBase):
    id: UUID
    driver_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True