import httpx
import polyline
from fastapi import HTTPException, status
from app.core.config import settings
from decimal import Decimal

async def fetch_route_details(
    origin_lat: float, origin_lng: float,
    destination_lat: float, destination_lng: float
) -> dict:
    url = "https://maps.googleapis.com/maps/api/directions/json"

    origin = f'{origin_lat},{origin_lng}'
    destination = f'{destination_lat},{destination_lng}'

    params = {
        "origin": origin,
        "destination": destination,
        "key": settings.GOOGLE_MAPS_API_KEY,
        "language": "pt-BR"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=502, detail="Erro de comunicação com o Google Maps.")

        data = response.json()

        if data.get("status") != "OK":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível localizar os endereços fornecidos."
            )

        route = data["routes"][0]
        leg = route["legs"][0]

        # Raw route metrics
        distance_km = Decimal(leg["distance"]["value"]) / Decimal(1000)
        duration_seconds = leg["duration"]["value"]

        # Add a 15% duration margin
        duration_with_margin = int((duration_seconds / 60) * 1.15)

        return {
            "origin_address": leg["start_address"],
            "destination_address": leg["end_address"],
            "distance_km": round(distance_km, 2),
            "duration_mins": duration_with_margin,
            "polyline": route["overview_polyline"]["points"],
            "start_location": leg["start_location"],
            "end_location": leg["end_location"]
        }

def polyline_to_linestring(polyline_str: str) -> str:
    coordinates = polyline.decode(polyline_str)
    wkt_points = ", ".join([f"{lon} {lat}" for lat,lon in coordinates])

    return f"SRID=4326;LINESTRING({wkt_points})"
