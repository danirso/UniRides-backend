import pytest
from fastapi import status

from app.core.security import create_access_token
from app.core.security import set_password_hash
from app.models.user import User


# ==========================================
# ENDPOINT TESTS: POST /rides/{id}/reviews
# ==========================================

def test_driver_reviews_passenger_success_201(client, driver_with_vehicle, completed_ride_with_passengers):
    ride, driver, first_passenger, _ = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    payload = {"reviewee_id": str(first_passenger.id), "rating": 5, "comment": "Ótimo passageiro"}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["rating"] == 5
    assert data["reviewee_id"] == str(first_passenger.id)
    assert data["reviewer_id"] == str(driver.id)


def test_passenger_reviews_driver_success_201(client, passenger_setup, completed_ride_with_passengers):
    ride, driver, _, _ = completed_ride_with_passengers
    _, passenger_headers = passenger_setup

    payload = {"reviewee_id": str(driver.id), "rating": 4, "comment": "Boa viagem"}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=passenger_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["rating"] == 4
    assert data["reviewee_id"] == str(driver.id)


def test_review_updates_user_average_rating(client, db_session, driver_with_vehicle, completed_ride_with_passengers):
    ride, _, first_passenger, _ = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    payload = {"reviewee_id": str(first_passenger.id), "rating": 4}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    db_session.refresh(first_passenger)
    assert first_passenger.rating_count == 1
    assert float(first_passenger.rating_avg) == 4.0


def test_review_before_ride_completion_400(client, driver_with_vehicle, scheduled_ride, passenger_setup):
    _, _, driver_headers = driver_with_vehicle
    first_passenger, _ = passenger_setup

    payload = {"reviewee_id": str(first_passenger.id), "rating": 5}

    response = client.post(f"/rides/{scheduled_ride.id}/reviews", json=payload, headers=driver_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "RIDE_NOT_COMPLETED"


def test_driver_reviews_nonparticipant_400(client, db_session, driver_with_vehicle, completed_ride_with_passengers):
    ride, _, _, _ = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    other_user = User(
        name="Estranho",
        email="estranho@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    payload = {"reviewee_id": str(other_user.id), "rating": 5}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_REVIEWEE"


def test_passenger_reviews_another_passenger_400(client, passenger_setup, completed_ride_with_passengers):
    ride, _, _, second_passenger = completed_ride_with_passengers
    _, first_passenger_headers = passenger_setup

    payload = {"reviewee_id": str(second_passenger.id), "rating": 3}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=first_passenger_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_REVIEWEE"


def test_nonparticipant_cannot_review_403(client, db_session, completed_ride_with_passengers):
    ride, driver, _, _ = completed_ride_with_passengers

    nonparticipant = User(
        name="Estranho",
        email="estranho2@puccampinas.edu.br",
        password_hash=set_password_hash("123"),
        is_email_verified=True
    )
    db_session.add(nonparticipant)
    db_session.commit()
    db_session.refresh(nonparticipant)
    nonparticipant_headers = {"Authorization": f"Bearer {create_access_token(data={'sub': str(nonparticipant.id)})}"}

    payload = {"reviewee_id": str(driver.id), "rating": 5}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=nonparticipant_headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ACCESS_DENIED"


def test_duplicate_review_400(client, driver_with_vehicle, completed_ride_with_passengers):
    ride, _, first_passenger, _ = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    payload = {"reviewee_id": str(first_passenger.id), "rating": 5}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "DUPLICATE_REVIEW"


def test_self_review_400(client, driver_with_vehicle, completed_ride_with_passengers):
    ride, driver, _, _ = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    payload = {"reviewee_id": str(driver.id), "rating": 5}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_REVIEWEE"


def test_rating_outside_valid_range_422(client, driver_with_vehicle, completed_ride_with_passengers):
    ride, _, first_passenger, _ = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    payload = {"reviewee_id": str(first_passenger.id), "rating": 6}

    response = client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ==========================================
# ENDPOINT TESTS: GET /rides/{id}/reviews/pending
# ==========================================

def test_driver_has_two_passengers_awaiting_reviews(client, driver_with_vehicle, completed_ride_with_passengers):
    ride, _, first_passenger, second_passenger = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    response = client.get(f"/rides/{ride.id}/reviews/pending", headers=driver_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    pending_user_ids = {item["user_id"] for item in data}
    assert pending_user_ids == {str(first_passenger.id), str(second_passenger.id)}
    assert all(item["role"] == "passenger" for item in data)


def test_passenger_has_only_driver_awaiting_review(client, passenger_setup, completed_ride_with_passengers):
    ride, driver, _, _ = completed_ride_with_passengers
    _, passenger_headers = passenger_setup

    response = client.get(f"/rides/{ride.id}/reviews/pending", headers=passenger_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == str(driver.id)
    assert data[0]["role"] == "driver"


def test_reviewed_participant_is_removed_from_pending_list(client, driver_with_vehicle, completed_ride_with_passengers):
    ride, _, first_passenger, second_passenger = completed_ride_with_passengers
    _, _, driver_headers = driver_with_vehicle

    payload = {"reviewee_id": str(first_passenger.id), "rating": 5}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=driver_headers)

    response = client.get(f"/rides/{ride.id}/reviews/pending", headers=driver_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == str(second_passenger.id)


def test_pending_reviews_empty_before_ride_completion(client, driver_with_vehicle, scheduled_ride):
    _, _, driver_headers = driver_with_vehicle

    response = client.get(f"/rides/{scheduled_ride.id}/reviews/pending", headers=driver_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

# ==========================================
# ENDPOINT TESTS: GET /users/{id}/reviews
# ==========================================

def test_list_received_reviews_newest_first(client, driver_with_vehicle, passenger_setup, completed_ride_with_passengers):
    ride, driver, first_passenger, _ = completed_ride_with_passengers
    _, passenger_headers = passenger_setup

    payload = {"reviewee_id": str(driver.id), "rating": 4, "comment": "Boa viagem"}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=passenger_headers)

    response = client.get(f"/users/{driver.id}/reviews", headers=passenger_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["rating"] == 4
    assert data[0]["comment"] == "Boa viagem"
    assert data[0]["reviewer_name"] == "Passageiro Teste"


def test_list_received_reviews_respects_limit(client, driver_with_vehicle, passenger_setup, completed_ride_with_passengers):
    ride, driver, _, _ = completed_ride_with_passengers
    _, passenger_headers = passenger_setup

    payload = {"reviewee_id": str(driver.id), "rating": 5}
    client.post(f"/rides/{ride.id}/reviews", json=payload, headers=passenger_headers)

    response = client.get(f"/users/{driver.id}/reviews?limit=0", headers=passenger_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_average_rating_after_reviews_from_two_users(client, db_session, passenger_setup, completed_ride_with_passengers):
    ride, driver, first_passenger, second_passenger = completed_ride_with_passengers
    _, first_passenger_headers = passenger_setup
    second_passenger_headers = {"Authorization": f"Bearer {create_access_token(data={'sub': str(second_passenger.id)})}"}

    client.post(f"/rides/{ride.id}/reviews", json={"reviewee_id": str(driver.id), "rating": 5}, headers=first_passenger_headers)
    client.post(f"/rides/{ride.id}/reviews", json={"reviewee_id": str(driver.id), "rating": 3}, headers=second_passenger_headers)

    db_session.refresh(driver)
    assert driver.rating_count == 2
    assert float(driver.rating_avg) == 4.0
