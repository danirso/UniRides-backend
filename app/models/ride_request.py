import enum
import uuid
from sqlalchemy import Column, ForeignKey, Enum, DateTime, String, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"

class RideRequest(Base):
    __tablename__ = "ride_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id", ondelete="CASCADE"), nullable=False)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    passenger_origin = Column(Geometry('POINT', srid=4326), nullable=False)
    passenger_destination = Column(Geometry('POINT', srid=4326), nullable=False)
    origin_address = Column(String, nullable=True)
    destination_address = Column(String, nullable=True)
    
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    passenger = relationship("User", foreign_keys=[passenger_id])
    ride = relationship("Ride", foreign_keys=[ride_id], overlaps="requests")