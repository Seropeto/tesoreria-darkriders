from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import crud, schemas, database, auth, models

router = APIRouter(
    prefix="/debts",
    tags=["Debts"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@router.post("/generate")
def generate_monthly_debts(
    month: int = Body(...), 
    year: int = Body(...), 
    amount: float = Body(...),
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_admin)
):
    count = crud.create_debt_bulk(db, month=month, year=year, amount=amount)
    return {"message": f"Generated/Verified debts for {count} active partners"}

@router.get("/pending", response_model=List[schemas.Debt])
def read_pending_debts(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # If partner, filter by their ID
    if current_user.role == 'partner':
        return crud.get_pending_debts(db, user_id=current_user.id)
    # If admin, return all
    return crud.get_pending_debts(db)
