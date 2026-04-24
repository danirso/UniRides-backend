import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID

class VehicleBase(BaseModel):
    brand: str = Field(..., description="Marca do veículo")
    model: str = Field(..., description="Modelo do veículo")
    color: str = Field(..., description="Cor do veículo")
    plate: str = Field(..., description="Placa do veículo")
    capacity: int = Field(..., gt=0, le=8, description="Capacidade máxima física de passageiros")

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str) -> str:
        plate = value.strip().upper()
        pattern = r"^[A-Z]{3}-?[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$"

        if not re.match(pattern,plate):
            raise ValueError("Placa com formato inválido. Utilize o formato AAA-1234 ou AAA1A23.")
        return plate.replace("-", "")
    
class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    plate: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0, le=8)
    
    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: Optional[str]) -> Optional[str]:
        plate = value.strip().upper()
        pattern = r"^[A-Z]{3}-?[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$"

        if not re.match(pattern,plate):
            raise ValueError("Placa com formato inválido. Utilize o formato AAA-1234 ou AAA1A23.")
        return plate.replace("-", "")

class VehicleResponse(VehicleBase):
    id: UUID
    owner_id: UUID

    model_config = ConfigDict(from_attributes=True)