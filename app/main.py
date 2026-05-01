from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.api.routers import auth, vehicle,user,ride,ride_request

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Unirides API",
    description="Backend do sistema de caronas universitárias",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(vehicle.router)
app.include_router(user.router)
app.include_router(ride.router)
app.include_router(ride_request.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "API rodando"}