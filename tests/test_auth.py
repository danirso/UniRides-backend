import pytest
from fastapi import status
from app.core.security import set_password_hash, create_access_token
from app.models.user import User

def test_register_201(client):
    payload = {
        "name": "Fulano de Tal",
        "email": "estudante@puccampinas.edu.br",
        "password": "senha_segura_123"
    }
    response = client.post("/auth/register", json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data

def test_login_200(client, db_session):
    email = "auth_test@puccampinas.edu.br"
    password = "password123"
    
    user = User(
        name="Teste Autenticacao",
        email=email,
        password_hash=set_password_hash(password),
        is_email_verified=True 
    )
    db_session.add(user)
    db_session.commit()

    login_data = {"username": email, "password": password}
    response = client.post("/auth/login", data=login_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_profile_200(client, db_session):
    email = "perfil@puccampinas.edu.br"
    user = User(
        name="Usuario Autenticado",
        email=email,
        password_hash=set_password_hash("123"),
        is_email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/users/me", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == email

def test_login_401(client, db_session):
    email = "erro@puccampinas.edu.com"
    user = User(
        name="Erro Login",
        email=email,
        password_hash=set_password_hash("correta"),
        is_email_verified=True
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", data={"username": email, "password": "errada"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED