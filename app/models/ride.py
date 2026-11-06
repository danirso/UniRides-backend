import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.database import Base

class RideStatus(str, enum.Enum):
    SCHEDULED = "agendada"
    IN_PROGRESS = "em_andamento"
    COMPLETED = "concluida"
    CANCELED = "cancelada"

class Ride(Base):
    __tablename__ = "rides"

    id = Column(UUID(as_uuid=True), primary_key=True,default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)

    departure_time = Column(DateTime, nullable=False)
    status = Column(String, default=RideStatus.SCHEDULED, nullable=False)
    available_seats = Column(Integer, nullable=False)
    max_detour_meters = Column(Integer, nullable=False, default=0)

    estimated_duration_mins = Column(Integer, nullable=True)
    distance_km = Column(Float)
    route_polyline = Column(String, nullable=True)

    origin_address = Column(String,nullable=False)
    destination_address = Column(String, nullable=False)

    origin_geom = Column(Geometry("POINT", srid=4326))
    destination_geom = Column(Geometry("POINT", srid=4326))
    route_geom = Column(Geometry(geometry_type="LINESTRING", srid=4326, nullable=True))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    driver = relationship("User", back_populates="rides")
    vehicle = relationship("Vehicle", back_populates="rides")
    requests = relationship("RideRequest", cascade="all, delete-orphan")

    def format_status_for_display(self):
        return self.status.replace("_", " ").capitalize()
