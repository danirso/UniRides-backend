from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class RideBase(BaseModel):
    available_seats: int = Field(..., gt=0, description="Available passenger seats.")
    max_detour_meters: int = Field(0, ge=0, description="Maximum allowed distance from the stored route, in meters.")
    departure_time: datetime = Field(..., description="Departure time.")

class RideCreate(RideBase):
    vehicle_id: UUID = Field(..., description="ID of a vehicle owned by the driver.")
    origin_address: str = Field(..., description="Pickup address.")
    destination_address: str = Field(..., description="Destination address.")
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
    estimated_duration_mins: int = Field(..., description="Estimated duration in minutes, including a 15% margin.")
    distance_km: float = Field(..., description="Route distance in kilometers.")
    route_polyline: str = Field(..., description="Encoded route polyline.")

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RideSearchRequest(BaseModel):
    origin_lat: float = Field(..., description="Passenger pickup latitude.")
    origin_lng: float = Field(..., description="Passenger pickup longitude.")
    destination_lat: float = Field(..., description="Passenger destination latitude.")
    destination_lng: float = Field(..., description="Passenger destination longitude.")
