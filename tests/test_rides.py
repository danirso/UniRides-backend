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
        "origin_address": "Av. Iguatemi, 777 - Vila Brandina, Campinas - SP",
        "destination_address": "Ac. Publico, 286 - Parque dos Jacarandás, Campinas - SP",
        "distance_km": 14.58,
        "duration_mins": 19,
        "polyline": r"hivjCba`~Gi@xJETGFMBE@eAe@i@[oAm@KHGVBTNLbCj@nB~@^NHPHVC\InA@VFh@X`BAj@Cj@W`AOb@]`ALVHFL@P@Tk@DOHYFUJcA|@eNNgDPsBVgBDsARqB^mFHcBCaAM}@Mi@c@aAkD_FoBcCuB_DcDkEs@eAsBoCaC_Dc@g@uA{AyEmFsAgB[c@k@kAQa@_@oA{BoJcAmEy@_Ds@mBIWAWAi@Di@P}ACc@QWq@Sc@MqAM}C_@g@DYJ_@VUVMb@@h@HVJNl@T`@PxCr@z@Rh@LLNJP@TOv@k@fC[fAWn@g@|@g@f@w@f@qBj@gF`By@ZcMfDkCz@gG`By@R{A`@SLQHwBv@uCfAIPuAb@IB]JkBh@yOrE}PbF_EjA}HzBcHrByNlEuEpAuFzAgCx@}HzBiLhDgHpBaBj@kAj@sAv@}AfAaBrAcAdAw@~@gEzFmCvDqBvCmDzEcF`HoAhBaBhCcAvA[d@w@rAe@lAy@zBa@hBYjBSlBIpBEnBOpLWtRQ|D_@tAQlAQhAu@nF[bBITm@jDwAdIe@jDSvBMxBQhFE|B@pEBxBN~CZjFb@`EAXBXJ|ANjE?LOj@QRi@ZUNKLO^On@Wr@QRg@TmBJmCTgD\qB^a@JqEjAeAVa@@YCc@IUKmA{@aEsDiCgC_DwCm@c@?SCYDs@@o@Lk@Pi@b@eA|B{EdAgC`AuBZ_@n@c@RSR[Pa@F[Hy@?UNw@|@yB`@aANk@PoAJ}AFIDSCUQOU?QLADYHkAReCRiAHUC?CCEMGK?E?",
        "start_location": {"lat": -22.8955, "lng": -47.0233},
        "end_location": {"lat": -22.8311, "lng": -47.0611}
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
    assert data["distance_km"] == 14.58
    assert data["route_polyline"] == r"hivjCba`~Gi@xJETGFMBE@eAe@i@[oAm@KHGVBTNLbCj@nB~@^NHPHVC\InA@VFh@X`BAj@Cj@W`AOb@]`ALVHFL@P@Tk@DOHYFUJcA|@eNNgDPsBVgBDsARqB^mFHcBCaAM}@Mi@c@aAkD_FoBcCuB_DcDkEs@eAsBoCaC_Dc@g@uA{AyEmFsAgB[c@k@kAQa@_@oA{BoJcAmEy@_Ds@mBIWAWAi@Di@P}ACc@QWq@Sc@MqAM}C_@g@DYJ_@VUVMb@@h@HVJNl@T`@PxCr@z@Rh@LLNJP@TOv@k@fC[fAWn@g@|@g@f@w@f@qBj@gF`By@ZcMfDkCz@gG`By@R{A`@SLQHwBv@uCfAIPuAb@IB]JkBh@yOrE}PbF_EjA}HzBcHrByNlEuEpAuFzAgCx@}HzBiLhDgHpBaBj@kAj@sAv@}AfAaBrAcAdAw@~@gEzFmCvDqBvCmDzEcF`HoAhBaBhCcAvA[d@w@rAe@lAy@zBa@hBYjBSlBIpBEnBOpLWtRQ|D_@tAQlAQhAu@nF[bBITm@jDwAdIe@jDSvBMxBQhFE|B@pEBxBN~CZjFb@`EAXBXJ|ANjE?LOj@QRi@ZUNKLO^On@Wr@QRg@TmBJmCTgD\qB^a@JqEjAeAVa@@YCc@IUKmA{@aEsDiCgC_DwCm@c@?SCYDs@@o@Lk@Pi@b@eA|B{EdAgC`AuBZ_@n@c@RSR[Pa@F[Hy@?UNw@|@yB`@aANk@PoAJ}AFIDSCUQOU?QLADYHkAReCRiAHUC?CCEMGK?E?"
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