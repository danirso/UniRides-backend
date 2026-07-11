import pytest
from fastapi import status

from app.core.security import create_access_token
from app.core.security import set_password_hash
from app.models.user import User


# ==========================================
# TESTES DA ROTA: POST /rides/{id}/reviews
# ==========================================

def test_motorista_avalia_passageiro_sucesso_201(client, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, motorista, passageiro1, _ = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    payload = {"reviewee_id": str(passageiro1.id), "rating": 5, "comment": "Ótimo passageiro"}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["rating"] == 5
    assert data["reviewee_id"] == str(passageiro1.id)
    assert data["reviewer_id"] == str(motorista.id)


def test_passageiro_avalia_motorista_sucesso_201(client, passageiro_setup, carona_concluida_com_passageiros):
    ride, motorista, _, _ = carona_concluida_com_passageiros
    _, headers_passageiro = passageiro_setup

    payload = {"reviewee_id": str(motorista.id), "rating": 4, "comment": "Boa viagem"}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_passageiro)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["rating"] == 4
    assert data["reviewee_id"] == str(motorista.id)


def test_avaliacao_atualiza_rating_medio_do_usuario(client, db_session, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, _, passageiro1, _ = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    payload = {"reviewee_id": str(passageiro1.id), "rating": 4}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    db_session.refresh(passageiro1)
    assert passageiro1.rating_count == 1
    assert float(passageiro1.rating_avg) == 4.0


def test_avaliacao_carona_nao_concluida_400(client, motorista_com_veiculo_setup, carona_agendada, passageiro_setup):
    _, _, headers_motorista = motorista_com_veiculo_setup
    passageiro1, _ = passageiro_setup

    payload = {"reviewee_id": str(passageiro1.id), "rating": 5}

    response = client.post(f"/rides/{carona_agendada.id}/reviews", json=payload, headers=headers_motorista)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "RIDE_NOT_COMPLETED"


def test_motorista_avaliar_passageiro_nao_participante_400(client, db_session, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, _, _, _ = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    outro_usuario = User(
        name="Estranho",
        email="estranho@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True
    )
    db_session.add(outro_usuario)
    db_session.commit()
    db_session.refresh(outro_usuario)

    payload = {"reviewee_id": str(outro_usuario.id), "rating": 5}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_REVIEWEE"


def test_passageiro_avaliar_outro_passageiro_400(client, passageiro_setup, carona_concluida_com_passageiros):
    ride, _, _, passageiro2 = carona_concluida_com_passageiros
    _, headers_passageiro1 = passageiro_setup

    payload = {"reviewee_id": str(passageiro2.id), "rating": 3}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_passageiro1)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_REVIEWEE"


def test_usuario_nao_participante_403(client, db_session, carona_concluida_com_passageiros):
    ride, motorista, _, _ = carona_concluida_com_passageiros

    estranho = User(
        name="Estranho",
        email="estranho2@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True
    )
    db_session.add(estranho)
    db_session.commit()
    db_session.refresh(estranho)
    headers_estranho = {"Authorization": f"Bearer {create_access_token(data={'sub': str(estranho.id)})}"}

    payload = {"reviewee_id": str(motorista.id), "rating": 5}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_estranho)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ACCESS_DENIED"


def test_avaliacao_duplicada_400(client, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, _, passageiro1, _ = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    payload = {"reviewee_id": str(passageiro1.id), "rating": 5}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "DUPLICATE_REVIEW"


def test_avaliar_a_si_mesmo_400(client, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, motorista, _, _ = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    payload = {"reviewee_id": str(motorista.id), "rating": 5}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_REVIEWEE"


def test_rating_fora_do_intervalo_422(client, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, _, passageiro1, _ = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    payload = {"reviewee_id": str(passageiro1.id), "rating": 6}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ==========================================
# TESTES DA ROTA: GET /rides/{id}/reviews/pending
# ==========================================

def test_motorista_ve_dois_passageiros_pendentes(client, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, _, passageiro1, passageiro2 = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    response = client.get(f"/rides/{ride.id}/reviews/pending", headers=headers_motorista)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    ids_pendentes = {item["user_id"] for item in data}
    assert ids_pendentes == {str(passageiro1.id), str(passageiro2.id)}
    assert all(item["role"] == "passenger" for item in data)


def test_passageiro_ve_apenas_motorista_pendente(client, passageiro_setup, carona_concluida_com_passageiros):
    ride, motorista, _, _ = carona_concluida_com_passageiros
    _, headers_passageiro = passageiro_setup

    response = client.get(f"/rides/{ride.id}/reviews/pending", headers=headers_passageiro)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == str(motorista.id)
    assert data[0]["role"] == "driver"


def test_pendencia_some_apos_avaliar(client, motorista_com_veiculo_setup, carona_concluida_com_passageiros):
    ride, _, passageiro1, passageiro2 = carona_concluida_com_passageiros
    _, _, headers_motorista = motorista_com_veiculo_setup

    payload = {"reviewee_id": str(passageiro1.id), "rating": 5}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_motorista)

    response = client.get(f"/rides/{ride.id}/reviews/pending", headers=headers_motorista)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == str(passageiro2.id)


def test_pendencia_vazia_para_carona_nao_concluida(client, motorista_com_veiculo_setup, carona_agendada):
    _, _, headers_motorista = motorista_com_veiculo_setup

    response = client.get(f"/rides/{carona_agendada.id}/reviews/pending", headers=headers_motorista)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
    
# ==========================================
# TESTES DA ROTA: GET /users/{id}/reviews
# ==========================================

def test_listar_avaliacoes_recebidas_mais_recentes_primeiro(client, motorista_com_veiculo_setup, passageiro_setup, carona_concluida_com_passageiros):
    ride, motorista, passageiro1, _ = carona_concluida_com_passageiros
    _, headers_passageiro = passageiro_setup

    payload = {"reviewee_id": str(motorista.id), "rating": 4, "comment": "Boa viagem"}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_passageiro)

    response = client.get(f"/users/{motorista.id}/reviews", headers=headers_passageiro)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["rating"] == 4
    assert data[0]["comment"] == "Boa viagem"
    assert data[0]["reviewer_name"] == "Passageiro Teste"


def test_listar_avaliacoes_respeita_limit(client, motorista_com_veiculo_setup, passageiro_setup, carona_concluida_com_passageiros):
    ride, motorista, _, _ = carona_concluida_com_passageiros
    _, headers_passageiro = passageiro_setup

    payload = {"reviewee_id": str(motorista.id), "rating": 5}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=headers_passageiro)

    response = client.get(f"/users/{motorista.id}/reviews?limit=0", headers=headers_passageiro)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_media_correta_apos_duas_avaliacoes_de_reviewers_diferentes(client, db_session, passageiro_setup, carona_concluida_com_passageiros):
    ride, motorista, passageiro1, passageiro2 = carona_concluida_com_passageiros
    _, headers_passageiro1 = passageiro_setup
    headers_passageiro2 = {"Authorization": f"Bearer {create_access_token(data={'sub': str(passageiro2.id)})}"}

    client.post(f"/rides/{ride.id}/reviews", json={"reviewee_id": str(motorista.id), "rating": 5}, headers=headers_passageiro1)
    client.post(f"/rides/{ride.id}/reviews", json={"reviewee_id": str(motorista.id), "rating": 3}, headers=headers_passageiro2)

    db_session.refresh(motorista)
    assert motorista.rating_count == 2
    assert float(motorista.rating_avg) == 4.0