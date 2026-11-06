import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import status
from unittest.mock import patch, AsyncMock

from app.models.ride import RideStatus

# ==========================================
# ENDPOINT TESTS: POST /rides/
# ==========================================

@patch("app.api.routers.ride.fetch_route_details", new_callable=AsyncMock)
def test_create_ride_success_201(mock_fetch_route_details,client, driver_with_vehicle):
    _, vehicle, headers = driver_with_vehicle

    mock_fetch_route_details.return_value = {
        "origin_address": "Av. Iguatemi, 777 - Vila Brandina, Campinas - SP",
        "destination_address": "Ac. Publico, 286 - Parque dos Jacarandás, Campinas - SP",
        "distance_km": 14.58,
        "duration_mins": 19,
        "polyline": r"hivjCba`~Gi@xJETGFMBE@eAe@i@[oAm@KHGVBTNLbCj@nB~@^NHPHVC\InA@VFh@X`BAj@Cj@W`AOb@]`ALVHFL@P@Tk@DOHYFUJcA|@eNNgDPsBVgBDsARqB^mFHcBCaAM}@Mi@c@aAkD_FoBcCuB_DcDkEs@eAsBoCaC_Dc@g@uA{AyEmFsAgB[c@k@kAQa@_@oA{BoJcAmEy@_Ds@mBIWAWAi@Di@P}ACc@QWq@Sc@MqAM}C_@g@DYJ_@VUVMb@@h@HVJNl@T`@PxCr@z@Rh@LLNJP@TOv@k@fC[fAWn@g@|@g@f@w@f@qBj@gF`By@ZcMfDkCz@gG`By@R{A`@SLQHwBv@uCfAIPuAb@IB]JkBh@yOrE}PbF_EjA}HzBcHrByNlEuEpAuFzAgCx@}HzBiLhDgHpBaBj@kAj@sAv@}AfAaBrAcAdAw@~@gEzFmCvDqBvCmDzEcF`HoAhBaBhCcAvA[d@w@rAe@lAy@zBa@hBYjBSlBIpBEnBOpLWtRQ|D_@tAQlAQhAu@nF[bBITm@jDwAdIe@jDSvBMxBQhFE|B@pEBxBN~CZjFb@`EAXBXJ|ANjE?LOj@QRi@ZUNKLO^On@Wr@QRg@TmBJmCTgD\qB^a@JqEjAeAVa@@YCc@IUKmA{@aEsDiCgC_DwCm@c@?SCYDs@@o@Lk@Pi@b@eA|B{EdAgC`AuBZ_@n@c@RSR[Pa@F[Hy@?UNw@|@yB`@aANk@PoAJ}AFIDSCUQOU?QLADYHkAReCRiAHUC?CCEMGK?E?",
        "start_location": {"lat": -22.8955, "lng": -47.0233},
        "end_location": {"lat": -22.8311, "lng": -47.0611}
    }

    payload = {
        "vehicle_id": str(vehicle.id),
        "origin_address": "Rua X",
        "destination_address": "Rua Y",
        "origin_lat": -22.8955,
        "origin_lng": -47.0233,
        "destination_lat": -22.8311,
        "destination_lng": -47.0611,
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "available_seats": 2,
        "max_detour_meters":500
    }

    response = client.post("/rides/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["distance_km"] == 14.58
    assert data["status"] == RideStatus.SCHEDULED.value
    mock_fetch_route_details.assert_called_once()

def test_create_ride_with_invalid_vehicle_403(client, driver_with_vehicle):
    _, _, headers = driver_with_vehicle
    payload = {
        "vehicle_id": str(uuid.uuid4()),
        "origin_address": "A",
        "destination_address": "B",
        "origin_lat": -22.8955,
        "origin_lng": -47.0233,
        "destination_lat": -22.8311,
        "destination_lng": -47.0611,
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "available_seats": 2
    }

    response = client.post("/rides/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "INVALID_VEHICLE"

def test_create_ride_exceeding_capacity_400(client, driver_with_vehicle):
    _, vehicle, headers = driver_with_vehicle
    payload = {
        "vehicle_id": str(vehicle.id),
        "origin_address": "A",
        "destination_address": "B",
        "origin_lat": -22.8955,
        "origin_lng": -47.0233,
        "destination_lat": -22.8311,
        "destination_lng": -47.0611,
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "available_seats": 5
    }

    response = client.post("/rides/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "CAPACITY_EXCEEDED"

# ==========================================
# ENDPOINT TESTS: PATCH /rides/{id}
# ==========================================

def test_update_ride_success_200(client, driver_with_vehicle, scheduled_ride):
    _, _, headers = driver_with_vehicle
    payload = {"destination_address": "Novo Destino"}

    response = client.patch(f"/rides/{scheduled_ride.id}", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["destination_address"] == "Novo Destino"

def test_update_ride_exceeding_capacity_400(client, driver_with_vehicle, scheduled_ride):
    _, _, headers = driver_with_vehicle
    payload = {"available_seats": 4}

    response = client.patch(f"/rides/{scheduled_ride.id}", json=payload, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "CAPACITY_EXCEEDED"

# ==========================================
# RIDE STATUS TRANSITION TESTS
# ==========================================

def test_start_ride_success_200(client, driver_with_vehicle, scheduled_ride):
    _, _, headers = driver_with_vehicle

    response = client.post(f"/rides/{scheduled_ride.id}/start", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RideStatus.IN_PROGRESS.value

def test_start_ride_with_invalid_status_400(client, driver_with_vehicle, scheduled_ride, db_session):
    _, _, headers = driver_with_vehicle

    scheduled_ride.status = RideStatus.IN_PROGRESS
    db_session.commit()

    response = client.post(f"/rides/{scheduled_ride.id}/start", headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "INVALID_STATUS_TRANSITION"

def test_complete_ride_success_200(client, driver_with_vehicle, scheduled_ride, db_session):
    _, _, headers = driver_with_vehicle

    scheduled_ride.status = RideStatus.IN_PROGRESS
    db_session.commit()

    response = client.post(f"/rides/{scheduled_ride.id}/complete", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RideStatus.COMPLETED.value

def test_cancel_ride_success_200(client, driver_with_vehicle, scheduled_ride):
    _, _, headers = driver_with_vehicle

    response = client.post(f"/rides/{scheduled_ride.id}/cancel", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == RideStatus.CANCELED.value

# ==========================================
# SPATIAL QUERY TESTS
# ==========================================

@patch("app.api.routers.ride.fetch_route_details", new_callable=AsyncMock)
def test_search_finds_matching_route(mock_fetch_route_details, client, driver_with_vehicle, passenger_setup):
    _, driver_vehicle, driver_headers = driver_with_vehicle
    _, passenger_headers = passenger_setup

    mock_fetch_route_details.return_value = {
        "origin_address": "Av. Iguatemi, 777 - Vila Brandina, Campinas - SP",
        "destination_address": "Ac. Publico, 286 - Parque dos Jacarandás, Campinas - SP",
        "distance_km": 14.58,
        "duration_mins": 19,
        "polyline": r"hivjCba`~Gi@xJETGFMBE@eAe@i@[oAm@KHGVBTNLbCj@nB~@^NHPHVC\InA@VFh@X`BAj@Cj@W`AOb@]`ALVHFL@P@Tk@DOHYFUJcA|@eNNgDPsBVgBDsARqB^mFHcBCaAM}@Mi@c@aAkD_FoBcCuB_DcDkEs@eAsBoCaC_Dc@g@uA{AyEmFsAgB[c@k@kAQa@_@oA{BoJcAmEy@_Ds@mBIWAWAi@Di@P}ACc@QWq@Sc@MqAM}C_@g@DYJ_@VUVMb@@h@HVJNl@T`@PxCr@z@Rh@LLNJP@TOv@k@fC[fAWn@g@|@g@f@w@f@qBj@gF`By@ZcMfDkCz@gG`By@R{A`@SLQHwBv@uCfAIPuAb@IB]JkBh@yOrE}PbF_EjA}HzBcHrByNlEuEpAuFzAgCx@}HzBiLhDgHpBaBj@kAj@sAv@}AfAaBrAcAdAw@~@gEzFmCvDqBvCmDzEcF`HoAhBaBhCcAvA[d@w@rAe@lAy@zBa@hBYjBSlBIpBEnBOpLWtRQ|D_@tAQlAQhAu@nF[bBITm@jDwAdIe@jDSvBMxBQhFE|B@pEBxBN~CZjFb@`EAXBXJ|ANjE?LOj@QRi@ZUNKLO^On@Wr@QRg@TmBJmCTgD\qB^a@JqEjAeAVa@@YCc@IUKmA{@aEsDiCgC_DwCm@c@?SCYDs@@o@Lk@Pi@b@eA|B{EdAgC`AuBZ_@n@c@RSR[Pa@F[Hy@?UNw@|@yB`@aANk@PoAJ}AFIDSCUQOU?QLADYHkAReCRiAHUC?CCEMGK?E?",
        "start_location": {"lat": -22.8955, "lng": -47.0233},
        "end_location": {"lat": -22.8311, "lng": -47.0611}
    }

    creation_payload = {
        "vehicle_id": str(driver_vehicle.id),
        "origin_address": "Iguatemi Campinas",
        "destination_address": "Parque dos Jacarandás",
        "origin_lat": -22.8955,
        "origin_lng": -47.0233,
        "destination_lat": -22.8311,
        "destination_lng": -47.0611,
        "departure_time": "2026-12-31T10:00:00Z",
        "available_seats": 2,
        "max_detour_meters": 1000
    }
    client.post("/rides/", json=creation_payload, headers=driver_headers)

    search_payload = {
        "origin_lat": -22.8950,
        "origin_lng": -47.0230,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615
    }

    response = client.post("/rides/search", json=search_payload, headers=passenger_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert data[0]["available_seats"] == 2

@patch("app.api.routers.ride.fetch_route_details", new_callable=AsyncMock)
def test_search_excludes_points_outside_route_distance(mock_fetch_route_details, client, driver_with_vehicle, passenger_setup):
    _, driver_vehicle, driver_headers = driver_with_vehicle
    _, passenger_headers = passenger_setup

    mock_fetch_route_details.return_value = {
        "origin_address": "Av. Iguatemi, 777 - Vila Brandina, Campinas - SP",
        "destination_address": "Ac. Publico, 286 - Parque dos Jacarandás, Campinas - SP",
        "distance_km": 14.58,
        "duration_mins": 19,
        "polyline": r"hivjCba`~Gi@xJETGFMBE@eAe@i@[oAm@KHGVBTNLbCj@nB~@^NHPHVC\InA@VFh@X`BAj@Cj@W`AOb@]`ALVHFL@P@Tk@DOHYFUJcA|@eNNgDPsBVgBDsARqB^mFHcBCaAM}@Mi@c@aAkD_FoBcCuB_DcDkEs@eAsBoCaC_Dc@g@uA{AyEmFsAgB[c@k@kAQa@_@oA{BoJcAmEy@_Ds@mBIWAWAi@Di@P}ACc@QWq@Sc@MqAM}C_@g@DYJ_@VUVMb@@h@HVJNl@T`@PxCr@z@Rh@LLNJP@TOv@k@fC[fAWn@g@|@g@f@w@f@qBj@gF`By@ZcMfDkCz@gG`By@R{A`@SLQHwBv@uCfAIPuAb@IB]JkBh@yOrE}PbF_EjA}HzBcHrByNlEuEpAuFzAgCx@}HzBiLhDgHpBaBj@kAj@sAv@}AfAaBrAcAdAw@~@gEzFmCvDqBvCmDzEcF`HoAhBaBhCcAvA[d@w@rAe@lAy@zBa@hBYjBSlBIpBEnBOpLWtRQ|D_@tAQlAQhAu@nF[bBITm@jDwAdIe@jDSvBMxBQhFE|B@pEBxBN~CZjFb@`EAXBXJ|ANjE?LOj@QRi@ZUNKLO^On@Wr@QRg@TmBJmCTgD\qB^a@JqEjAeAVa@@YCc@IUKmA{@aEsDiCgC_DwCm@c@?SCYDs@@o@Lk@Pi@b@eA|B{EdAgC`AuBZ_@n@c@RSR[Pa@F[Hy@?UNw@|@yB`@aANk@PoAJ}AFIDSCUQOU?QLADYHkAReCRiAHUC?CCEMGK?E?",
        "start_location": {"lat": -22.8955, "lng": -47.0233},
        "end_location": {"lat": -22.8311, "lng": -47.0611}
    }

    creation_payload = {
        "vehicle_id": str(driver_vehicle.id),
        "origin_address": "Iguatemi Campinas",
        "destination_address": "Parque dos Jacarandás",
        "origin_lat": -22.8955,
        "origin_lng": -47.0233,
        "destination_lat": -22.8311,
        "destination_lng": -47.0611,
        "departure_time": "2026-12-31T10:00:00Z",
        "available_seats": 2,
        "max_detour_meters": 1000
    }

    client.post("/rides/", json=creation_payload, headers=driver_headers)

    search_payload = {
        "origin_lat": -23.5505,
        "origin_lng": -46.6333,
        "destination_lat": -22.8315,
        "destination_lng": -47.0615
    }

    response = client.post("/rides/search", json=search_payload, headers=passenger_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

@patch("app.api.routers.ride.fetch_route_details", new_callable=AsyncMock)
def test_search_excludes_opposite_travel_direction(mock_fetch_route_details, client, driver_with_vehicle, passenger_setup):
    _, driver_vehicle, driver_headers = driver_with_vehicle
    _, passenger_headers = passenger_setup

    mock_fetch_route_details.return_value = {
        "origin_address": "Av. Iguatemi, 777 - Vila Brandina, Campinas - SP",
        "destination_address": "Ac. Publico, 286 - Parque dos Jacarandás, Campinas - SP",
        "distance_km": 14.58,
        "duration_mins": 19,
        "polyline": r"hivjCba`~Gi@xJETGFMBE@eAe@i@[oAm@KHGVBTNLbCj@nB~@^NHPHVC\InA@VFh@X`BAj@Cj@W`AOb@]`ALVHFL@P@Tk@DOHYFUJcA|@eNNgDPsBVgBDsARqB^mFHcBCaAM}@Mi@c@aAkD_FoBcCuB_DcDkEs@eAsBoCaC_Dc@g@uA{AyEmFsAgB[c@k@kAQa@_@oA{BoJcAmEy@_Ds@mBIWAWAi@Di@P}ACc@QWq@Sc@MqAM}C_@g@DYJ_@VUVMb@@h@HVJNl@T`@PxCr@z@Rh@LLNJP@TOv@k@fC[fAWn@g@|@g@f@w@f@qBj@gF`By@ZcMfDkCz@gG`By@R{A`@SLQHwBv@uCfAIPuAb@IB]JkBh@yOrE}PbF_EjA}HzBcHrByNlEuEpAuFzAgCx@}HzBiLhDgHpBaBj@kAj@sAv@}AfAaBrAcAdAw@~@gEzFmCvDqBvCmDzEcF`HoAhBaBhCcAvA[d@w@rAe@lAy@zBa@hBYjBSlBIpBEnBOpLWtRQ|D_@tAQlAQhAu@nF[bBITm@jDwAdIe@jDSvBMxBQhFE|B@pEBxBN~CZjFb@`EAXBXJ|ANjE?LOj@QRi@ZUNKLO^On@Wr@QRg@TmBJmCTgD\qB^a@JqEjAeAVa@@YCc@IUKmA{@aEsDiCgC_DwCm@c@?SCYDs@@o@Lk@Pi@b@eA|B{EdAgC`AuBZ_@n@c@RSR[Pa@F[Hy@?UNw@|@yB`@aANk@PoAJ}AFIDSCUQOU?QLADYHkAReCRiAHUC?CCEMGK?E?",
        "start_location": {"lat": -22.8955, "lng": -47.0233},
        "end_location": {"lat": -22.8311, "lng": -47.0611}
    }

    creation_payload = {
        "vehicle_id": str(driver_vehicle.id),
        "origin_address": "Iguatemi Campinas",
        "destination_address": "Parque dos Jacarandás",
        "origin_lat": -22.8955,
        "origin_lng": -47.0233,
        "destination_lat": -22.8311,
        "destination_lng": -47.0611,
        "departure_time": "2026-12-31T10:00:00Z",
        "available_seats": 2,
        "max_detour_meters": 1000
    }

    client.post("/rides/", json=creation_payload, headers=driver_headers)

    search_payload = {
        "origin_lat": -22.8315,
        "origin_lng": -47.0615,
        "destination_lat": -22.8950,
        "destination_lng": -47.0230
    }

    response = client.post("/rides/search", json=search_payload, headers=passenger_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0
