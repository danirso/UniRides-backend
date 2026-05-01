from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.ride_request import RequestStatus

class PassengerSnippet(BaseModel):
    id:UUID
    name:str
    
    model_config = ConfigDict(from_attributes=True)
    
class RideSnippet(BaseModel):
    id:UUID
    origin_address:str
    destination_address:str
    departure_time:datetime
    
    model_config = ConfigDict(from_attributes=True) 

class RideRequestCreate(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float

class RideRequestResponse(BaseModel):
    id: UUID
    ride_id: UUID
    passenger_id: UUID
    status: RequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class RideRequestWithPassenger(RideRequestResponse):
    passenger: PassengerSnippet
    
    model_config = ConfigDict(from_attributes=True)

class RideRequestWithRide(RideRequestResponse):
    ride: RideSnippet
    
    model_config = ConfigDict(from_attributes=True)