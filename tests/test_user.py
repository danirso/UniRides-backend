import pytest
from fastapi import status
from app.models.user import User
from app.core.security import set_password_hash, create_access_token

# ==========================================
# FIXTURES LOCAIS
# ==========================================

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

# ==========================================
# TESTES DA ROTA: GET /users/me
# ==========================================

def test_ver_perfil_sucesso_200(client, auth_setup):
    user, headers = auth_setup
    
    response = client.get("/users/me", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user.email
    assert data["name"] == user.name

def test_ver_perfil_sem_token_401(client):
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ==========================================
# TESTES DA ROTA: PATCH /users/me
# ==========================================

def test_atualizar_perfil_dados_simples_200(client, auth_setup, db_session):
    user, headers = auth_setup
    
    payload = {"name": "Nome Atualizado"}
    response = client.patch("/users/me", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    db_session.refresh(user)
    assert user.name == "Nome Atualizado"

def test_atualizar_perfil_senha_200(client, auth_setup, db_session):
    user, headers = auth_setup
    hash_antigo = user.password_hash
    
    payload = {"password": "nova_senha_segura"}
    response = client.patch("/users/me", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    db_session.refresh(user)
    assert user.password_hash != hash_antigo

def test_atualizar_perfil_email_invalida_verificacao_200(client, auth_setup, db_session):
    user, headers = auth_setup
    
    payload = {"email": "novo_email@puccampinas.edu.br"}
    response = client.patch("/users/me", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    db_session.refresh(user)
    assert user.email == "novo_email@puccampinas.edu.br"
    assert user.is_email_verified is False
    assert user.activation_token is not None

def test_atualizar_perfil_email_existente_400(client, auth_setup, db_session):
    _, headers = auth_setup
    
    outro_user = User(
        name="Outro Usuario",
        email="ja_existe@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(outro_user)
    db_session.commit()

    payload = {"email": "ja_existe@puccampinas.edu.br"}
    response = client.patch("/users/me", json=payload, headers=headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Este e-mail já está em uso por outro usuário."

# ==========================================
# TESTES DA ROTA: DELETE /users/me
# ==========================================

def test_deletar_perfil_sucesso_204(client, auth_setup, db_session):
    user, headers = auth_setup
    
    response = client.delete("/users/me", headers=headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    usuario_deletado = db_session.query(User).filter(User.id == user.id).first()
    assert usuario_deletado is None

def test_deletar_perfil_sem_token_401(client):
    response = client.delete("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED