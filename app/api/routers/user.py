from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.dependencies import get_current_user
from app.core.security import set_password_hash 

router = APIRouter(prefix="/users", tags=["Usuários"])

@router.get("/me", response_model=UserResponse)
def Ver_perfil(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def Atualizar_perfil(user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        new_password = set_password_hash(update_data.pop("password"))
        update_data["password_hash"] = new_password
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deletar_perfil(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(current_user)
    db.commit()