import pytest
from fastapi import status
from app.models.user import User
from app.core.security import set_password_hash

# ==========================================
# ENDPOINT TESTS: GET /users/me
# ==========================================

def test_get_profile_success_200(client, auth_setup):
    user, headers = auth_setup

    response = client.get("/users/me", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user.email
    assert data["name"] == user.name

def test_get_profile_without_token_401(client):
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ==========================================
# ENDPOINT TESTS: PATCH /users/me
# ==========================================

def test_update_profile_details_200(client, auth_setup, db_session):
    user, headers = auth_setup

    payload = {"name": "Nome Atualizado"}
    response = client.patch("/users/me", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK

    db_session.refresh(user)
    assert user.name == "Nome Atualizado"

def test_update_password_200(client, auth_setup, db_session):
    user, headers = auth_setup
    old_password_hash = user.password_hash

    payload = {"password": "nova_senha_segura"}
    response = client.patch("/users/me", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK

    db_session.refresh(user)
    assert user.password_hash != old_password_hash

def test_update_email_requires_reverification_200(client, auth_setup, db_session):
    user, headers = auth_setup

    payload = {"email": "novo_email@puccampinas.edu.br"}
    response = client.patch("/users/me", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK

    db_session.refresh(user)
    assert user.email == "novo_email@puccampinas.edu.br"
    assert user.is_email_verified is False
    assert user.activation_token is not None

def test_update_profile_with_existing_email_400(client, auth_setup, db_session):
    _, headers = auth_setup

    other_user = User(
        name="Outro Usuario",
        email="ja_existe@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True,
        can_drive=False
    )
    db_session.add(other_user)
    db_session.commit()

    payload = {"email": "ja_existe@puccampinas.edu.br"}
    response = client.patch("/users/me", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "EMAIL_ALREADY_IN_USE"

# ==========================================
# ENDPOINT TESTS: DELETE /users/me
# ==========================================

def test_delete_profile_success_204(client, auth_setup, db_session):
    user, headers = auth_setup

    response = client.delete("/users/me", headers=headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_user = db_session.query(User).filter(User.id == user.id).first()
    assert deleted_user is None

def test_delete_profile_without_token_401(client):
    response = client.delete("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
