from fastapi import FastAPI
from app.db.database import Base, engine
from app.models.user import User
from app.models.vehicle import Vehicle
from app.api.routers import auth
from app.api.routers import vehicle

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TCC: Caronas Universitárias API")

app.include_router(auth.router)
app.include_router(vehicle.router)

@app.get("/")
def root():
    return {"message": "API rodando"}