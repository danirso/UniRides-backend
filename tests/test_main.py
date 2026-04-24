from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_deve_retornar_200():
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "API rodando"}