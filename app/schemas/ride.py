from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class RideBase(BaseModel):
    available_seats: int = Field(..., gt=0, description="Número de assentos disponíveis")
    max_detour_meters: int = Field(0, ge=0, description="Desvio máximo aceitável em metros")
    departure_time: datetime = Field(..., description="Horário de partida")

class RideCreate(RideBase):
    vehicle_id: UUID = Field(..., description="ID do veículo utilizado na carona")
    origin_address: str = Field(..., description="Endereço de partida por extenso")
    destination_address: str = Field(..., description="Endereço de chegada por extenso")
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    departure_time: datetime
    available_seats: int = Field(..., gt=0)
    max_detour_meters: int = Field(default=1000)

class RideUpdate(BaseModel):
    available_seats: Optional[int] = Field(None, gt=0)
    max_detour_meters: Optional[int] = Field(None, ge=0)
    departure_time: Optional[datetime] = None
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    vehicle_id: Optional[UUID] = None
    
class DriverSnippet(BaseModel):
    id:UUID
    name:str
    rating_avg: float = 0.0
    rating_count: int = 0    
    model_config = ConfigDict(from_attributes=True)
    
class RideResponse(RideBase):
    id: UUID
    driver_id: UUID
    driver: DriverSnippet
    vehicle_id: UUID
    status: str
    origin_address: str
    destination_address: str
    estimated_duration_mins: int = Field(..., description="Tempo com margem de 15% aplicada")
    distance_km: float = Field(..., description="Distância exata da rota")
    route_polyline: str = Field(..., description="String para desenhar a linha no mapa")
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class RideSearchRequest(BaseModel):
    origin_lat: float = Field(..., description="Latitude da origem do passageiro")
    origin_lng: float = Field(..., description="Longitude da origem do passageiro")
    destination_lat: float = Field(..., description="Latitude do destino do passageiro")
    destination_lng: float = Field(..., description="Longitude do destino do passageiro")