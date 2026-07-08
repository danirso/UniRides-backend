import pytest
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.ride import Ride, RideStatus
from app.models.ride_request import RideRequest,RequestStatus
from app.core.security import set_password_hash, create_access_token

TEST_SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL

if not TEST_SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("A variável TEST_DATABASE_URL não foi encontrada")


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
def motorista_com_veiculo_setup(db_session):
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
    
    veiculo = Vehicle(
        plate="ABC1234",
        brand="VW",
        model="Polo",
        color="Branco",
        capacity=3,
        owner_id=user.id
    )
    db_session.add(veiculo)
    db_session.commit()
    db_session.refresh(veiculo)
    
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    return user, veiculo, headers

@pytest.fixture
def carona_agendada(db_session, motorista_com_veiculo_setup):
    user, veiculo, _ = motorista_com_veiculo_setup
    
    ride = Ride(
        driver_id=user.id,
        vehicle_id=veiculo.id,
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
def motorista_setup(db_session):
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
def motorista2_setup(db_session):
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
def passageiro_setup(db_session):
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
def passageiro2_setup(db_session):
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
def carona_com_vagas(db_session, motorista_com_veiculo_setup):
    user, veiculo, _ = motorista_com_veiculo_setup
    
    ride = Ride(
        driver_id=user.id,
        vehicle_id=veiculo.id,
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
def solicitacao_pendente(db_session, carona_com_vagas, passageiro_setup):
    passageiro, _ = passageiro_setup
    req = RideRequest(
        ride_id=carona_com_vagas.id,
        passenger_id=passageiro.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.PENDING
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)
    return req

@pytest.fixture
def carona_concluida_com_passageiros(db_session, motorista_com_veiculo_setup, passageiro_setup, passageiro2_setup):
    motorista, veiculo, _ = motorista_com_veiculo_setup
    passageiro1, _ = passageiro_setup
    passageiro2, _ = passageiro2_setup

    ride = Ride(
        driver_id=motorista.id,
        vehicle_id=veiculo.id,
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
        passenger_id=passageiro1.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.ACCEPTED
    )
    req2 = RideRequest(
        ride_id=ride.id,
        passenger_id=passageiro2.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.ACCEPTED
    )
    db_session.add_all([req1, req2])
    db_session.commit()

    return ride, motorista, passageiro1, passageiro2