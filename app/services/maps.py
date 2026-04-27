import httpx
import polyline
from fastapi import HTTPException, status
from app.core.config import settings
from decimal import Decimal

async def buscar_detalhes_da_rota(origem: str, destino: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/directions/json"
    
    params = {
        "origin": origem,
        "destination": destino,
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

        # Dados brutos
        distancia_km = Decimal(leg["distance"]["value"]) / Decimal(1000)
        duracao_segundos = leg["duration"]["value"]

        # Margem de desvio de 15%
        duracao_com_margem = int((duracao_segundos / 60) * 1.15)

        return {
            "origin_address": leg["start_address"],
            "destination_address": leg["end_address"],
            "distance_km": round(distancia_km, 2),
            "duration_mins": duracao_com_margem,
            "polyline": route["overview_polyline"]["points"],
            "start_location": leg["start_location"],
            "end_location": leg["end_location"]
        }
        
def polyline_to_linestring(polyline_str: str) -> str:
    coordenadas = polyline.decode(polyline_str)
    pontos_wkt = ", ".join([f"{lon} {lat}" for lat,lon in coordenadas])
    
    return f"SRID=4326;LINESTRING({pontos_wkt})"