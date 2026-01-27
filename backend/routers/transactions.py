from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
import crud, schemas, database, auth, models

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@router.post("/", response_model=schemas.Transaction)
def create_transaction(
    transaction: schemas.TransactionCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_admin)
):
    # Only Admin (verified by Depends)
    try:
        print(f"[DEBUG] Creating Transaction. UserID: {current_user.id}, Payload: {transaction}")
        user_id = current_user.id
        if transaction.user_id:
            user_id = transaction.user_id
            print(f"[DEBUG] Override UserID: {user_id}")
                
        # Process Debts if linked
        if transaction.debt_ids:
            print(f"[DEBUG] Processing Debts: {transaction.debt_ids}")
            for debt_id in transaction.debt_ids:
                crud.pay_debt(db, debt_id, commit=False) # DEFER COMMIT
            print("[DEBUG] Debts marked as paid (not committed).")

        print("[DEBUG] Calling crud.create_transaction")
        # Commit everything here at the end
        # Pass current_admin.id as creator_id
        result = crud.create_transaction(db=db, transaction=transaction, creator_id=current_user.id, commit=True)
        print("[DEBUG] Transaction created AND debts committed successfully.")
        return result
    except Exception as e:
        print(f"[ERROR] Transaction failed: {e}")
        db.rollback() # ROLLBACK ON FAILURE
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions(skip: int = 0, limit: int = 50, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # All active users can see transaction history (Transparency)
    query = db.query(models.Transaction).options(
        joinedload(models.Transaction.user),
        joinedload(models.Transaction.created_by)
    )

    if current_user.role == 'partner':
        from sqlalchemy import or_, and_
        # Rule: See ALL expenses OR (Incomes that belong to me)
        query = query.filter(
            or_(
                models.Transaction.type == 'expense',
                and_(
                    models.Transaction.type == 'income',
                    models.Transaction.user_id == current_user.id
                )
            )
        )
    
    return query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()
