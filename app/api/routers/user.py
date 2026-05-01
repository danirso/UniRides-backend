import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.exceptions import UserException
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.dependencies import get_current_user
from app.core.security import set_password_hash
from app.utils.email import send_activation_email

router = APIRouter(prefix="/users", tags=["Usuários"])

@router.get("/me", response_model=UserResponse)
def Ver_Perfil(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def Atualizar_Perfil(
    user_in: UserUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        new_password_hash = set_password_hash(update_data.pop("password"))
        update_data["password_hash"] = new_password_hash

    email_changed = False
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = db.query(User).filter(User.email == update_data["email"]).first()
        if existing_user:
            raise UserException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="EMAIL_ALREADY_IN_USE",
                message="Este e-mail já está em uso por outro usuário."
            )
        
        email_changed = True
        update_data["is_email_verified"] = False
        update_data["activation_token"] = secrets.token_urlsafe(32)
        
        brt_tz = ZoneInfo("America/Sao_Paulo")
        update_data["token_expires_at"] = datetime.now(brt_tz) + timedelta(hours=1)

    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    if email_changed:
        send_activation_email(
            email_to=current_user.email,
            user_name=current_user.name,
            token=current_user.activation_token,
            background_tasks=background_tasks
        )
        
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def Deletar_Perfil(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(current_user)
    db.commit()
    return