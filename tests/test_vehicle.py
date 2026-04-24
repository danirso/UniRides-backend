import pytest
from fastapi import status
from app.models.user import User
from app.models.vehicle import Vehicle
from app.core.security import set_password_hash, create_access_token

@pytest.fixture
def auth_headers(db_session):
    user = User(
        name="Motorista Teste",
        email="motorista@puccampinas.edu.br",
        password_hash=set_password_hash("123456"),
        is_email_verified=True,
        can_drive=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    
    return {"Authorization": f"Bearer {token}"}


def test_add_vehicle_201(client, auth_headers):
    payload = {
        "brand": "Fiat",
        "model": "Argo",
        "color": "Branco",
        "plate": "ABC1234",
        "capacity": 4
    }
    
    response = client.post("/vehicles/", json=payload, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["plate"] == payload["plate"]
    assert "id" in data

def test_add_vehicle_401(client):
    payload = {
        "brand": "Honda",
        "model": "Civic",
        "color": "Preto",
        "plate": "XYZ9876",
        "capacity": 4
    }
    response = client.post("/vehicles/", json=payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
# def test_get_vehicles_200(client, auth_headers, db_session):
#     vehicle = Vehicle(
#         owner_id="",
#         brand="BYD",
#         model="King",
#         color="Preto",     
#         plate="RVR9A44",
#         capacity="4"
#     )
#     db_session.add(vehicle)
#     db_session.commmit()
#     db_session.refresh(vehicle)
    
    
#     response = client.get("/vehicles/")
    
#     assert response.status_code == status.HTTP_200_OK