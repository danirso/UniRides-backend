import secrets
from datetime import datetime,timedelta,timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.email import send_activation_email
from app.core.security import set_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(user_in: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado."
        )
    token = secrets.token_urlsafe(32)
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=set_password_hash(user_in.password),
        can_drive=user_in.can_drive,
        activation_token=token,
        token_expires_at=expiration
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    send_activation_email(new_user.email, new_user.name, token, background_tasks)
    
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_email_verified:
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Sua conta ainda não foi ativada. Por favor, verifique seu e-mail institucional." 
        )
        
    token_jwt = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": token_jwt, "token_type": "bearer"}

@router.get("/verify-email")
def verificar_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.activation_token == token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado.")
    
    if user.token_expires_at and user.token_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="O token de ativação expirou. Solicite um novo.")
    
    user.is_email_verified = True
    user.activation_token = None
    user.token_expires_at = None
    
    db.commit()
    
    return {"message": "E-mail verificado com sucesso! Sua conta está ativada."}