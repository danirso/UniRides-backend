import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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
    # Estimativas
    estimated_duration_mins = Column(Integer, nullable=True)
    estimated_distance_km = Column(Numeric(precision=10, scale=2), nullable=True)
    # Campos de Geometria (Armazenados como String por hora)
    start_point = Column(String, nullable=True) # Ex: "POINT(-47.06 -22.89)"
    end_point = Column(String, nullable=True)   # Ex: "POINT(-47.01 -22.92)"
    route_line = Column(String, nullable=True)  # Ex: "LINESTRING(...)"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    driver = relationship("User", back_populates="rides")
    vehicle = relationship("Vehicle", back_populates="rides")

    def formatar_status_para_exibicao(self):
        return self.status.replace("_", " ").capitalize()