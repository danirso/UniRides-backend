from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.core.config import settings
from app.api.routers import auth, vehicle,user,ride,ride_request, review

Base.metadata.create_all(bind=engine)

is_dev = settings.ENVIRONMENT == "dev"

app = FastAPI(
    title="Unirides API",
    description="Backend do sistema de caronas universitárias",
    version="1.0.0",
    docs_url="/docs" if is_dev else None,
    redoc_url="/redoc" if is_dev else None,
    openapi_url="/openapi.json" if is_dev else None,
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
app.include_router(review.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "API rodando"}