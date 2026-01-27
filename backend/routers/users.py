from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud, schemas, database, auth, models

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, role: str = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Only admin should see full list? Or partners need to see other partners?
    # Requirement RF-05: Need list of partners for creating Income.
    return crud.get_users(db, skip=skip, limit=limit, role=role)

@router.post("/", response_model=schemas.User)
def create_partner(user: schemas.UserCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin)):
    # Only Admin can create users via API
    # Requirement: Assign generic password on creation.
    # We overwrite whatever password might be in schema or ignore it.
    # Let's assume frontend allows setting it or we set it here.
    # Prompt said "Al momento de crear un socio se asignará una clave generica"
    # But schemas.UserCreate has password field. I'll overwrite it.
    user.password = "DarkRiders123" 
    
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Mapping "Tesorero" -> admin, "Socio" -> partner done in frontend or here?
    # Requirement: "Tipo de Socio (Socio, Tesorero)"
    # Let's ensure role is mapped correctly.
    if user.role not in ['admin', 'partner']:
        user.role = 'partner'

    return crud.create_user(db=db, user=user)

@router.put("/{user_id}", response_model=schemas.User)
def update_user_endpoint(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin)):
    # Only Admin can update generic user info
    updated_user = crud.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.put("/me/password", response_model=schemas.User)
def change_password(password_data: schemas.UserUpdatePassword, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if not crud.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    return crud.update_password(db, user_id=current_user.id, new_password=password_data.new_password)

@router.get("/{user_id}/debts", response_model=List[schemas.Debt])
def read_user_debts(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Can see own debts or Admin can see any
    if current_user.role != 'admin' and current_user.id != user_id:
         raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_pending_debts(db, user_id=user_id)
