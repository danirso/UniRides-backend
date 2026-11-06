from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.core.config import settings
from app.api.routers import auth, vehicle,user,ride,ride_request, review

Base.metadata.create_all(bind=engine)

is_dev = settings.ENVIRONMENT == "dev"

app = FastAPI(
    title="Unirides API",
    description="""University ride-sharing API with PostGIS route matching.

## Try it locally
1. Run `./scripts/run-local.sh` and register `driver@example.com` or `passenger@example.com`.
2. Open [Mailpit](http://127.0.0.1:8025), then follow the activation link.
3. Click **Authorize** and use the registered email as `username` and the account password.
4. Register a vehicle as a driver, create a ride, then request a seat as a passenger.

`example.com` accounts require both development mode and the explicit local-email option.
Creating a ride requires your own Google Maps Directions key; other flows can be explored without it.
Business-rule error responses use `detail.code` and `detail.message`; validation errors return HTTP 422.
""",
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

@app.get("/", tags=["Health"], summary="Check API health", description="Return a basic API status response.")
def root():
    return {"status": "ok", "message": "API rodando"}
