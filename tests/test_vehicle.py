import pytest
import uuid
from fastapi import status
from app.models.user import User
from app.models.vehicle import Vehicle
from app.core.security import set_password_hash, create_access_token


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

# ==========================================
# TESTES DA ROTA: POST /vehicles/
# ==========================================

def test_registrar_veiculo_sucesso_201(client, motorista_setup):
    _, headers = motorista_setup
    payload = {
        "plate": "ABC1234",
        "brand": "Fiat",
        "model": "Argo",
        "color": "Branco",
        "capacity": 4
    }
    
    response = client.post("/vehicles/", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["plate"] == payload["plate"]
    assert "owner_id" in data

def test_registrar_veiculo_nao_motorista_403(client, passageiro_setup):
    _, headers = passageiro_setup
    payload = {"plate": "XYZ-9999", "brand": "VW", "model": "Gol", "color": "Preto", "capacity": 4}
    
    response = client.post("/vehicles/", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Usuário não cadastrado como motorista."

def test_registrar_veiculo_placa_duplicada_400(client, motorista_setup, db_session):
    user, headers = motorista_setup
    
    veiculo = Vehicle(plate="DUP0000", brand="Ford", model="Ka", color="Prata", capacity=4, owner_id=user.id)
    db_session.add(veiculo)
    db_session.commit()

    payload = {"plate": "DUP0000", "brand": "Chevrolet", "model": "Onix", "color": "Azul", "capacity": 4}
    response = client.post("/vehicles/", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Placa já cadastrada no sistema."

# ==========================================
# TESTES DA ROTA: GET /vehicles/
# ==========================================

def test_listar_veiculos_isolamento_200(client, motorista_setup,motorista2_setup, db_session):
    motorista,motorista_headers = motorista_setup
    motorista2,motorista2_headers = motorista2_setup
    
    v1 = Vehicle(plate="LOG0001", brand="A", model="B", color="C", capacity=2, owner_id=motorista.id)
    v2 = Vehicle(plate="OUT0002", brand="X", model="Y", color="Z", capacity=2, owner_id=motorista2.id)
    
    db_session.add_all([v1, v2])
    db_session.commit()

    response = client.get("/vehicles/", headers=motorista_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["plate"] == "LOG0001"

# ==========================================
# TESTES DA ROTA: PATCH /vehicles/{id}
# ==========================================

def test_atualizar_veiculo_sucesso_200(client, motorista_setup, db_session):
    motorista, headers = motorista_setup
    veiculo = Vehicle(plate="UPD1234", brand="VW", model="Polo", color="Preto", capacity=4, owner_id=motorista.id)
    db_session.add(veiculo)
    db_session.commit()

    payload = {"color": "Vermelho"}
    response = client.patch(f"/vehicles/{veiculo.id}", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["color"] == "Vermelho"

def test_atualizar_veiculo_outro_dono_404(client, motorista_setup, motorista2_setup, db_session):
    _, headers = motorista_setup
    motorista2,motorista2_headers = motorista2_setup
  
    veiculo = Vehicle(plate="DEN0L00", brand="A", model="B", color="C", capacity=2, owner_id=motorista2.id)
    db_session.add(veiculo)
    db_session.commit()

    payload = {"color": "Rosa"}
    response = client.patch(f"/vehicles/{veiculo.id}", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

# ==========================================
# TESTES DA ROTA: DELETE /vehicles/{id}
# ==========================================

def test_deletar_veiculo_sucesso_204(client, motorista_setup, db_session):
    motorista, headers = motorista_setup
    veiculo = Vehicle(plate="DEL9999", brand="A", model="B", color="C", capacity=2, owner_id=motorista.id)
    db_session.add(veiculo)
    db_session.commit()

    response = client.delete(f"/vehicles/{veiculo.id}", headers=headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    veiculo_db = db_session.query(Vehicle).filter(Vehicle.id == veiculo.id).first()
    assert veiculo_db is None

def test_deletar_veiculo_inexistente_404(client, motorista_setup):
    _, headers = motorista_setup
    id_falso = uuid.uuid4()
    
    response = client.delete(f"/vehicles/{id_falso}", headers=headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND