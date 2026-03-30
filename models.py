from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    is_motorista = Column(Boolean, default=False) 
   
    caronas_oferecidas = relationship("Carona", back_populates="motorista")


class Carona(Base):
    __tablename__ = "caronas"

    id = Column(Integer, primary_key=True, index=True)
    motorista_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    origem = Column(String, nullable=False) 
    destino = Column(String, nullable=False)
    vagas = Column(Integer, nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow)

    motorista = relationship("Usuario", back_populates="caronas_oferecidas")