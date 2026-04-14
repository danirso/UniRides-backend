import uuid
from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_email_verified = Column(Boolean, default=False)
    activation_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    can_drive = Column(Boolean, default=False)
    rating_avg = Column(Numeric(3, 2), default=0.0)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")