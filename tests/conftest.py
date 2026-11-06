import pytest
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch
from urllib.parse import urlsplit

from app.core.config import settings

TEST_SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL

if not TEST_SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("A variável TEST_DATABASE_URL não foi encontrada")


def _supabase_project_ref(database_url: str) -> str | None:
    parsed = urlsplit(database_url)
    host = (parsed.hostname or "").lower()

    if host.endswith(".pooler.supabase.com"):
        username = parsed.username or ""
        return username.rsplit(".", 1)[-1] if "." in username else None

    if host.endswith(".supabase.co"):
        parts = host.split(".")
        return parts[1] if parts[0] == "db" else parts[0]

    return None


production_ref = _supabase_project_ref(settings.DATABASE_URL)
test_ref = _supabase_project_ref(TEST_SQLALCHEMY_DATABASE_URL)

if production_ref and test_ref and production_ref == test_ref:
    raise RuntimeError("DATABASE_URL e TEST_DATABASE_URL apontam para o mesmo projeto Supabase")

settings.DATABASE_URL = TEST_SQLALCHEMY_DATABASE_URL

from app.db.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.ride import Ride, RideStatus
from app.models.ride_request import RideRequest,RequestStatus
from app.core.security import set_password_hash, create_access_token

engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
    yield

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def mock_send_email():
    with patch("fastapi_mail.FastMail.send_message") as mock:
        yield mock

@pytest.fixture
def driver_with_vehicle(db_session):
    user = User(
        name="Motorista Carona",
        email="driver@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    vehicle = Vehicle(
        plate="ABC1234",
        brand="VW",
        model="Polo",
        color="Branco",
        capacity=3,
        owner_id=user.id
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    return user, vehicle, headers

@pytest.fixture
def scheduled_ride(db_session, driver_with_vehicle):
    user, vehicle, _ = driver_with_vehicle

    ride = Ride(
        driver_id=user.id,
        vehicle_id=vehicle.id,
        origin_address="Campus I",
        destination_address="Centro",
        distance_km=5.0,
        route_polyline="Linha Azul Fake",
        estimated_duration_mins=15,
        departure_time=datetime.now(timezone.utc) + timedelta(hours=2),
        available_seats=2,
        status=RideStatus.SCHEDULED
    )
    db_session.add(ride)
    db_session.commit()
    db_session.refresh(ride)
    return ride

@pytest.fixture
def auth_setup(db_session):
    user = User(
        name="Usuario Perfil",
        email="perfil@puccampinas.edu.br",
        password_hash=set_password_hash("senha_original"),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    return user, headers

@pytest.fixture
def driver_setup(db_session):
    user = User(
        name="Motorista Teste",
        email="motorista@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, {"Authorization": f"Bearer {token}"}

@pytest.fixture
def second_driver_setup(db_session):
    user = User(
        name="Motorista Teste2",
        email="motorista2@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, {"Authorization": f"Bearer {token}"}

@pytest.fixture
def passenger_setup(db_session):
    user = User(
        name="Passageiro Teste",
        email="passageiro@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, {"Authorization": f"Bearer {token}"}

@pytest.fixture
def second_passenger_setup(db_session):
    user = User(
        name="Passageiro Teste 2",
        email="passageiro2@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ride_with_available_seats(db_session, driver_with_vehicle):
    user, vehicle, _ = driver_with_vehicle

    ride = Ride(
        driver_id=user.id,
        vehicle_id=vehicle.id,
        origin_address="Origem",
        destination_address="Destino",
        distance_km=10.0,
        route_polyline="Polyline",
        estimated_duration_mins=30,
        departure_time=datetime.now(timezone.utc) + timedelta(hours=2),
        available_seats=2,
        status=RideStatus.SCHEDULED,
        origin_geom="SRID=4326;POINT(-47.0233 -22.8955)",
        destination_geom="SRID=4326;POINT(-47.0611 -22.8311)",
        route_geom="SRID=4326;LINESTRING(-47.0233 -22.8955, -47.0611 -22.8311)"
    )
    db_session.add(ride)
    db_session.commit()
    db_session.refresh(ride)
    return ride

@pytest.fixture
def pending_ride_request(db_session, ride_with_available_seats, passenger_setup):
    passenger, _ = passenger_setup
    req = RideRequest(
        ride_id=ride_with_available_seats.id,
        passenger_id=passenger.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.PENDING
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)
    return req

@pytest.fixture
def completed_ride_with_passengers(db_session, driver_with_vehicle, passenger_setup, second_passenger_setup):
    driver, vehicle, _ = driver_with_vehicle
    first_passenger, _ = passenger_setup
    second_passenger, _ = second_passenger_setup

    ride = Ride(
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        origin_address="Campus I",
        destination_address="Centro",
        distance_km=5.0,
        route_polyline="Linha Azul Fake",
        estimated_duration_mins=15,
        departure_time=datetime.now(timezone.utc) - timedelta(hours=2),
        available_seats=0,
        status=RideStatus.COMPLETED
    )
    db_session.add(ride)
    db_session.commit()
    db_session.refresh(ride)

    req1 = RideRequest(
        ride_id=ride.id,
        passenger_id=first_passenger.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.ACCEPTED
    )
    req2 = RideRequest(
        ride_id=ride.id,
        passenger_id=second_passenger.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.ACCEPTED
    )
    db_session.add_all([req1, req2])
    db_session.commit()

    return ride, driver, first_passenger, second_passenger
