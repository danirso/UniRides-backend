from fastapi import FastAPI

# Cria a instância da nossa API
app = FastAPI(title="API Caronas TCC")

# Cria a nossa primeira rota (o endereço base)
@app.get("/")
def read_root():
    return {"status": "API rodando perfeitamente! Bora pro TCC."}

@app.get("/caronas")
def listar_caronas():
    return [
        {"id": 1, "motorista": "Carlos", "destino": "Campus Principal", "vagas": 3},
        {"id": 2, "motorista": "Ana", "destino": "República", "vagas": 1}
    ]