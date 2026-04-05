from fastapi import FastAPI
from app.db.database import Base, engine
from app.models.User import User
from app.api.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TCC: Caronas Universitárias API")

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "API rodando e conectada à estrutura base."}