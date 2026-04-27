import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import status
from unittest.mock import patch, AsyncMock

from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.ride import Ride, RideStatus
from app.core.security import set_password_hash, create_access_token

# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def motorista_setup(db_session):
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
def carona_agendada(db_session, motorista_setup):
    user, veiculo, _ = motorista_setup
    
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

# ==========================================
# TESTES DA ROTA: POST /rides/
# ==========================================

@patch("app.api.routers.ride.buscar_detalhes_da_rota", new_callable=AsyncMock)
def test_criar_carona_sucesso_201(mock_buscar_detalhes,client, motorista_setup):
    _, veiculo, headers = motorista_setup
    
    mock_buscar_detalhes.return_value = {
        "origin_address": "Endereço Origem Mock",
        "destination_address": "Endereço Destino Mock",
        "distance_km": 10.0,
        "duration_mins": 15,
        "polyline": "linha_azul_falsa",
        "start_location": {"lat": -22.0, "lng": -47.0},
        "end_location": {"lat": -22.1, "lng": -47.1}
    }
    
    payload = {
        "vehicle_id": str(veiculo.id),
        "origin_address": "Rua X",
        "destination_address": "Rua Y",
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "available_seats": 2,
        "max_detour_meters":500
    }
    
    response = client.post("/rides/", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["distance_km"] == 10.0
    assert data["route_polyline"] == "linha_azul_falsa"
    assert data["status"] == RideStatus.SCHEDULED.value
    mock_buscar_detalhes.assert_called_once()

def test_criar_carona_veiculo_invalido_403(client, motorista_setup):
    _, _, headers = motorista_setup
    payload = {
        "vehicle_id": str(uuid.uuid4()),
        "origin_address": "A",
        "destination_address": "B",
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "available_seats": 2
    }
    
    response = client.post("/rides/", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_criar_carona_capacidade_excedida_400(client, motorista_setup):
    _, veiculo, headers = motorista_setup
    payload = {
        "vehicle_id": str(veiculo.id),
        "origin_address": "A",
        "destination_address": "B",
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "available_seats": 5 
    }
    
    response = client.post("/rides/", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

# ==========================================
# TESTES DA ROTA: PATCH /rides/{id}
# ==========================================

def test_atualizar_carona_sucesso_200(client, motorista_setup, carona_agendada):
    _, _, headers = motorista_setup
    payload = {"destination_address": "Novo Destino"}
    
    response = client.patch(f"/rides/{carona_agendada.id}", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["destination_address"] == "Novo Destino"

def test_atualizar_carona_capacidade_excedida_400(client, motorista_setup, carona_agendada):
    _, _, headers = motorista_setup
    payload = {"available_seats": 4}
    
    response = client.patch(f"/rides/{carona_agendada.id}", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

# ==========================================
# TESTES DE TRANSIÇÃO DE ESTADO
# ==========================================

def test_iniciar_carona_sucesso_200(client, motorista_setup, carona_agendada):
    _, _, headers = motorista_setup
    
    response = client.post(f"/rides/{carona_agendada.id}/start", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RideStatus.IN_PROGRESS.value

def test_iniciar_carona_erro_estado_invalido_400(client, motorista_setup, carona_agendada, db_session):
    _, _, headers = motorista_setup
    
    carona_agendada.status = RideStatus.IN_PROGRESS
    db_session.commit()
    
    response = client.post(f"/rides/{carona_agendada.id}/start", headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_finalizar_carona_sucesso_200(client, motorista_setup, carona_agendada, db_session):
    _, _, headers = motorista_setup
    
    carona_agendada.status = RideStatus.IN_PROGRESS
    db_session.commit()
    
    response = client.post(f"/rides/{carona_agendada.id}/complete", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RideStatus.COMPLETED.value

def test_cancelar_carona_sucesso_200(client, motorista_setup, carona_agendada):
    _, _, headers = motorista_setup
    
    response = client.post(f"/rides/{carona_agendada.id}/cancel", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RideStatus.CANCELED.value