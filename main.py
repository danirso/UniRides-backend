from fastapi import FastAPI
from schemas.carona import CaronaResponse, CaronaBase
import models
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Caronas TCC")

@app.get("/")
def read_root():
    return {"status": "API rodando"}

@app.get("/caronas", response_model=list[CaronaResponse])
def listar_caronas():
    return [
        {"id": 1, "motorista": "Carlos", "destino": "Campus Principal", "vagas": 3},
        {"id": 2, "motorista": "Ana", "destino": "República", "vagas": 1}
    ]
    
@app.post("/caronas", response_model=CaronaResponse)
def criar_carona(nova_carona: CaronaBase):
    return{
        "id": 99,
        "motorista": nova_carona.motorista,
        "destino": nova_carona.destino,
        "vagas": nova_carona.vagas
    }