import pytest
import uuid
from fastapi import status
from app.models.vehicle import Vehicle

# ==========================================
# ENDPOINT TESTS: POST /vehicles/
# ==========================================

def test_register_vehicle_success_201(client, driver_setup):
    _, headers = driver_setup
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

def test_non_driver_registers_vehicle_403(client, passenger_setup):
    _, headers = passenger_setup
    payload = {"plate": "XYZ-9999", "brand": "VW", "model": "Gol", "color": "Preto", "capacity": 4}

    response = client.post("/vehicles/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "USER_NOT_DRIVER"

def test_register_vehicle_with_duplicate_plate_400(client, driver_setup, db_session):
    user, headers = driver_setup

    vehicle = Vehicle(plate="DUP0000", brand="Ford", model="Ka", color="Prata", capacity=4, owner_id=user.id)
    db_session.add(vehicle)
    db_session.commit()

    payload = {"plate": "DUP0000", "brand": "Chevrolet", "model": "Onix", "color": "Azul", "capacity": 4}
    response = client.post("/vehicles/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "PLATE_ALREADY_REGISTERED"

# ==========================================
# ENDPOINT TESTS: GET /vehicles/
# ==========================================

def test_list_vehicles_returns_only_owned_vehicles_200(client, driver_setup,second_driver_setup, db_session):
    driver,driver_headers = driver_setup
    second_driver,second_driver_headers = second_driver_setup

    v1 = Vehicle(plate="LOG0001", brand="A", model="B", color="C", capacity=2, owner_id=driver.id)
    v2 = Vehicle(plate="OUT0002", brand="X", model="Y", color="Z", capacity=2, owner_id=second_driver.id)

    db_session.add_all([v1, v2])
    db_session.commit()

    response = client.get("/vehicles/", headers=driver_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 1
    assert data[0]["plate"] == "LOG0001"

# ==========================================
# ENDPOINT TESTS: PATCH /vehicles/{id}
# ==========================================

def test_update_vehicle_success_200(client, driver_setup, db_session):
    driver, headers = driver_setup
    vehicle = Vehicle(plate="UPD1234", brand="VW", model="Polo", color="Preto", capacity=4, owner_id=driver.id)
    db_session.add(vehicle)
    db_session.commit()

    payload = {"color": "Vermelho"}
    response = client.patch(f"/vehicles/{vehicle.id}", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["color"] == "Vermelho"

def test_update_another_users_vehicle_404(client, driver_setup, second_driver_setup, db_session):
    _, headers = driver_setup
    second_driver,second_driver_headers = second_driver_setup

    vehicle = Vehicle(plate="DEN0L00", brand="A", model="B", color="C", capacity=2, owner_id=second_driver.id)
    db_session.add(vehicle)
    db_session.commit()

    payload = {"color": "Rosa"}
    response = client.patch(f"/vehicles/{vehicle.id}", json=payload, headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["code"] == "VEHICLE_NOT_FOUND"

# ==========================================
# ENDPOINT TESTS: DELETE /vehicles/{id}
# ==========================================

def test_delete_vehicle_success_204(client, driver_setup, db_session):
    driver, headers = driver_setup
    vehicle = Vehicle(plate="DEL9999", brand="A", model="B", color="C", capacity=2, owner_id=driver.id)
    db_session.add(vehicle)
    db_session.commit()

    response = client.delete(f"/vehicles/{vehicle.id}", headers=headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    stored_vehicle = db_session.query(Vehicle).filter(Vehicle.id == vehicle.id).first()
    assert stored_vehicle is None

def test_delete_missing_vehicle_404(client, driver_setup):
    _, headers = driver_setup
    missing_id = uuid.uuid4()

    response = client.delete(f"/vehicles/{missing_id}", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["code"] == "VEHICLE_NOT_FOUND"
