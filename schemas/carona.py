from pydantic import BaseModel

class CaronaBase(BaseModel):
    motorista: str
    destino: str
    vagas: int

class CaronaResponse(CaronaBase):
    id: int

    class Config:
        from_attributes = True