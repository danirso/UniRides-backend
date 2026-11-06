import pytest
from fastapi import status
from app.models.ride_request import RideRequest, RequestStatus

# ==========================================
# SEAT REQUEST TESTS (PASSENGER)
# ==========================================

def test_request_seat_success_201(client, passenger_setup, ride_with_available_seats):
    _, headers = passenger_setup

    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == RequestStatus.PENDING.value
    assert data["ride_id"] == str(ride_with_available_seats.id)

def test_request_seat_on_full_ride_400(client, passenger_setup, ride_with_available_seats, db_session):
    _, headers = passenger_setup

    ride_with_available_seats.available_seats = 0
    db_session.commit()

    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "RIDE_UNAVAILABLE"

def test_driver_requests_seat_on_own_ride_400(client, driver_with_vehicle, ride_with_available_seats):
    _, _, headers = driver_with_vehicle

    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_PASSENGER"

def test_duplicate_seat_request_400(client, passenger_setup, ride_with_available_seats, db_session):
    passenger, headers = passenger_setup

    existing_request = RideRequest(
        ride_id=ride_with_available_seats.id,
        passenger_id=passenger.id,
        passenger_origin="SRID=4326;POINT(-47.0230 -22.8950)",
        passenger_destination="SRID=4326;POINT(-47.0615 -22.8315)",
        status=RequestStatus.PENDING
    )
    db_session.add(existing_request)
    db_session.commit()

    payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615,
        "origin_address": "Rua Teste, 123 - Campinas, SP",
        "destination_address": "Av. Destino, 456 - Campinas, SP"
    }

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "DUPLICATE_REQUEST"

# ==========================================
# DRIVER ACTION TESTS (ACCEPT/REJECT)
# ==========================================

def test_driver_accepts_request_success_200(client, driver_with_vehicle, ride_with_available_seats, pending_ride_request, db_session):
    _, _, headers = driver_with_vehicle

    initial_seats = ride_with_available_seats.available_seats

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests/{pending_ride_request.id}/accept", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RequestStatus.ACCEPTED.value

    db_session.refresh(ride_with_available_seats)
    assert ride_with_available_seats.available_seats == initial_seats - 1

def test_driver_accepts_request_for_full_ride_400(client, driver_with_vehicle, ride_with_available_seats, pending_ride_request, db_session):
    _, _, headers = driver_with_vehicle

    ride_with_available_seats.available_seats = 0
    db_session.commit()

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests/{pending_ride_request.id}/accept", headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "RIDE_FULL"

def test_driver_rejects_request_success_200(client, driver_with_vehicle, ride_with_available_seats, pending_ride_request, db_session):
    _, _, headers = driver_with_vehicle
    initial_seats = ride_with_available_seats.available_seats

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests/{pending_ride_request.id}/reject", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RequestStatus.REJECTED.value


    db_session.refresh(ride_with_available_seats)
    assert ride_with_available_seats.available_seats == initial_seats

# ==========================================
# PASSENGER ACTION TESTS (CANCEL)
# ==========================================

def test_cancel_pending_request_preserves_seats_200(client, passenger_setup, ride_with_available_seats, pending_ride_request, db_session):
    _, headers = passenger_setup
    initial_seats = ride_with_available_seats.available_seats

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests/{pending_ride_request.id}/cancel", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RequestStatus.CANCELED.value

    # Cancelling a pending request must not change the seat count.
    db_session.refresh(ride_with_available_seats)
    assert ride_with_available_seats.available_seats == initial_seats

def test_cancel_accepted_request_returns_seat_200(client, passenger_setup, ride_with_available_seats, pending_ride_request, db_session):
    _, headers = passenger_setup

    # Set up an accepted request and reserve its seat.
    pending_ride_request.status = RequestStatus.ACCEPTED
    ride_with_available_seats.available_seats -= 1
    db_session.commit()
    seats_after_acceptance = ride_with_available_seats.available_seats

    response = client.post(f"/rides/{ride_with_available_seats.id}/requests/{pending_ride_request.id}/cancel", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    # The cancelled reservation must return its seat to the ride.
    db_session.refresh(ride_with_available_seats)
    assert ride_with_available_seats.available_seats == seats_after_acceptance + 1

def test_cancel_request_with_different_ride_id_404(
    client, passenger_setup, ride_with_available_seats, scheduled_ride, pending_ride_request, db_session
):
    _, headers = passenger_setup
    pending_ride_request.status = RequestStatus.ACCEPTED
    ride_with_available_seats.available_seats -= 1
    db_session.commit()
    original_ride_seats = ride_with_available_seats.available_seats
    other_ride_seats = scheduled_ride.available_seats

    response = client.post(
        f"/rides/{scheduled_ride.id}/requests/{pending_ride_request.id}/cancel",
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["code"] == "REQUEST_NOT_FOUND"
    db_session.refresh(pending_ride_request)
    db_session.refresh(ride_with_available_seats)
    db_session.refresh(scheduled_ride)
    assert pending_ride_request.status == RequestStatus.ACCEPTED
    assert ride_with_available_seats.available_seats == original_ride_seats
    assert scheduled_ride.available_seats == other_ride_seats


# ==========================================
# TESTES: GET /rides/{ride_id}/requests (Driver view)
# ==========================================

def test_driver_lists_ride_requests_200(client, driver_with_vehicle, ride_with_available_seats, pending_ride_request):
    _, _, headers = driver_with_vehicle

    response = client.get(f"/rides/{ride_with_available_seats.id}/list-requests", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    assert data[0]["id"] == str(pending_ride_request.id)

    assert "passenger" in data[0]
    assert "name" in data[0]["passenger"]

def test_non_driver_cannot_list_ride_requests_403(client, passenger_setup, ride_with_available_seats):
    _, headers = passenger_setup

    response = client.get(f"/rides/{ride_with_available_seats.id}/list-requests", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ACCESS_DENIED"

# ==========================================
# TESTES: GET /requests/me (Passenger view)
# ==========================================

def test_list_my_ride_requests_success_200(client, passenger_setup, ride_with_available_seats, pending_ride_request):
    _, headers = passenger_setup

    response = client.get("/rides/requests/me", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    assert data[0]["id"] == str(pending_ride_request.id)

    assert "ride" in data[0]
    assert "origin_address" in data[0]["ride"]
    assert "destination_address" in data[0]["ride"]
