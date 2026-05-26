import pytest
from fastapi import status
from app.models.ride_request import RideRequest, RequestStatus

# ==========================================
# TESTES: SOLICITAÇÃO DE VAGA (PASSAGEIRO)
# ==========================================

def test_solicitar_vaga_sucesso_201(client, passageiro_setup, carona_com_vagas):
    _, headers = passageiro_setup
    
    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == RequestStatus.PENDING.value
    assert data["ride_id"] == str(carona_com_vagas.id)

def test_solicitar_vaga_carona_cheia_400(client, passageiro_setup, carona_com_vagas, db_session):
    _, headers = passageiro_setup
    
    carona_com_vagas.available_seats = 0
    db_session.commit()
    
    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "RIDE_UNAVAILABLE"

def test_solicitar_vaga_motorista_na_propria_carona_400(client, motorista_com_veiculo_setup, carona_com_vagas):
    _, _, headers = motorista_com_veiculo_setup
    
    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_PASSENGER"

def test_solicitar_vaga_duplicada_400(client, passageiro_setup, carona_com_vagas, db_session):
    passageiro, headers = passageiro_setup
    
    request_existente = RideRequest(
        ride_id=carona_com_vagas.id,
        passenger_id=passageiro.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.PENDING
    )
    db_session.add(request_existente)
    db_session.commit()
    
    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "DUPLICATE_REQUEST"

# ==========================================
# TESTES: AÇÕES DO MOTORISTA (ACEITAR/REJEITAR)
# ==========================================

def test_motorista_aceita_solicitacao_sucesso_200(client, motorista_com_veiculo_setup, carona_com_vagas, solicitacao_pendente, db_session):
    _, _, headers = motorista_com_veiculo_setup
    
    vagas_iniciais = carona_com_vagas.available_seats
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests/{solicitacao_pendente.id}/accept", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RequestStatus.ACCEPTED.value
    
    db_session.refresh(carona_com_vagas)
    assert carona_com_vagas.available_seats == vagas_iniciais - 1

def test_motorista_aceita_solicitacao_carona_cheia_400(client, motorista_com_veiculo_setup, carona_com_vagas, solicitacao_pendente, db_session):
    _, _, headers = motorista_com_veiculo_setup
    
    carona_com_vagas.available_seats = 0
    db_session.commit()
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests/{solicitacao_pendente.id}/accept", headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "RIDE_FULL"

def test_motorista_rejeita_solicitacao_sucesso_200(client, motorista_com_veiculo_setup, carona_com_vagas, solicitacao_pendente, db_session):
    _, _, headers = motorista_com_veiculo_setup
    vagas_iniciais = carona_com_vagas.available_seats
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests/{solicitacao_pendente.id}/reject", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RequestStatus.REJECTED.value
    

    db_session.refresh(carona_com_vagas)
    assert carona_com_vagas.available_seats == vagas_iniciais

# ==========================================
# TESTES: AÇÕES DO PASSAGEIRO (CANCELAR)
# ==========================================

def test_passageiro_cancela_solicitacao_pendente_200(client, passageiro_setup, carona_com_vagas, solicitacao_pendente, db_session):
    _, headers = passageiro_setup
    vagas_iniciais = carona_com_vagas.available_seats
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests/{solicitacao_pendente.id}/cancel", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RequestStatus.CANCELED.value
    
    # Vagas não devem mudar se a solicitação era só pendente
    db_session.refresh(carona_com_vagas)
    assert carona_com_vagas.available_seats == vagas_iniciais

def test_passageiro_cancela_solicitacao_aceita_reembolsa_vaga_200(client, passageiro_setup, carona_com_vagas, solicitacao_pendente, db_session):
    _, headers = passageiro_setup
    
    # Força a solicitação a estar aceita e desconta a vaga
    solicitacao_pendente.status = RequestStatus.ACCEPTED
    carona_com_vagas.available_seats -= 1
    db_session.commit()
    vagas_apos_aceite = carona_com_vagas.available_seats
    
    response = client.post(f"/rides/{carona_com_vagas.id}/requests/{solicitacao_pendente.id}/cancel", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verifica se a vaga foi devolvida ("reembolsada") para a carona
    db_session.refresh(carona_com_vagas)
    assert carona_com_vagas.available_seats == vagas_apos_aceite + 1
    
# ==========================================
# TESTES: GET /rides/{ride_id}/requests (Visão do Motorista)
# ==========================================

def test_listar_solicitacoes_da_carona_sucesso_200(client, motorista_com_veiculo_setup, carona_com_vagas, solicitacao_pendente):
    _, _, headers = motorista_com_veiculo_setup
    
    response = client.get(f"/rides/{carona_com_vagas.id}/list-requests", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    
    assert data[0]["id"] == str(solicitacao_pendente.id)
    
    assert "passenger" in data[0]
    assert "name" in data[0]["passenger"]

def test_listar_solicitacoes_nao_sendo_o_motorista_403(client, passageiro_setup, carona_com_vagas):
    _, headers = passageiro_setup
    
    response = client.get(f"/rides/{carona_com_vagas.id}/list-requests", headers=headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ACCESS_DENIED"

# ==========================================
# TESTES: GET /requests/me (Visão do Passageiro)
# ==========================================

def test_listar_minhas_solicitacoes_sucesso_200(client, passageiro_setup, carona_com_vagas, solicitacao_pendente):
    _, headers = passageiro_setup
    
    response = client.get("/rides/requests/me", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    
    assert data[0]["id"] == str(solicitacao_pendente.id)
    
    assert "ride" in data[0]
    assert "origin_address" in data[0]["ride"]
    assert "destination_address" in data[0]["ride"]