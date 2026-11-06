import pytest
from datetime import datetime, timedelta, timezone
from fastapi import status
from app.models.user import User
from app.core.security import set_password_hash

# ==========================================
# ENDPOINT TESTS: /auth/register
# ==========================================

def test_register_201(client, db_session):
    payload = {
        "name": "Usuario Novo",
        "email": "novo@puccampinas.edu.br",
        "password": "senha_segura_123"
    }
    response = client.post("/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data

def test_register_duplicate_email_400(client, db_session):
    user = User(
        name="Usuario Existente",
        email="duplicado@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        can_drive=False,
        is_email_verified=True
    )
    db_session.add(user)
    db_session.commit()

    payload = {
        "name": "Tentativa Duplicada",
        "email": "duplicado@puccampinas.edu.br",
        "password": "outrasenha",
        "can_drive": True
    }
    response = client.post("/auth/register", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "EMAIL_ALREADY_REGISTERED"

def test_register_invalid_payload_422(client, db_session):
    payload = {
        "name": "Usuario Invalido",
        "email": "invalido@puccampinas.edu.br"
    }
    response = client.post("/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

# ==========================================
# ENDPOINT TESTS: /auth/login
# ==========================================

def test_login_success_200(client, db_session):
    email = "login_ok@puccampinas.edu.br"
    password = "password123"

    user = User(
        name="Login Success",
        email=email,
        password_hash=set_password_hash(password),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", data={"username": email, "password": password})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials_401(client, db_session):
    email = "login_erro@puccampinas.edu.br"
    user = User(
        name="Erro Login",
        email=email,
        password_hash=set_password_hash("senha_correta"),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", data={"username": email, "password": "senha_errada"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"

def test_login_unverified_email_403(client, db_session):
    email = "unverified@puccampinas.edu.br"
    password = "password123"

    user = User(
        name="Nao Verificado",
        email=email,
        password_hash=set_password_hash(password),
        is_email_verified=False,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", data={"username": email, "password": password})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"

# ==========================================
# ENDPOINT TESTS: /auth/verify-email
# ==========================================

def test_verify_email_success_200(client, db_session):
    token = "token_valido_123"
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)

    user = User(
        name="Ativacao Teste",
        email="ativacao@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=False,
        activation_token=token,
        token_expires_at=expiration,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()

    response = client.get(f"/auth/verify-email?token={token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "E-mail verificado com sucesso! Sua conta está ativada."

def test_verify_email_invalid_token_400(client, db_session):
    response = client.get("/auth/verify-email?token=token_inexistente")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_ACTIVATION_TOKEN"

def test_verify_email_expired_token_400(client, db_session):
    token = "token_expirado_123"
    expiration = datetime.now(timezone.utc) - timedelta(hours=3)

    user = User(
        name="Expirado Teste",
        email="expirado@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=False,
        activation_token=token,
        token_expires_at=expiration,
        can_drive=False
    )
    db_session.add(user)
    db_session.commit()

    response = client.get(f"/auth/verify-email?token={token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "EXPIRED_ACTIVATION_TOKEN"
