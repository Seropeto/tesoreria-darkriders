from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import database, auth, models

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(auth.get_current_active_user)] # Admin only primarily?
)

@router.get("/summary")
def get_summary(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # RF-10: KPIs (Admin view primarily)
    # If partner, maybe show their own debt?
    
    total_income = db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.type == "income").scalar() or 0
    total_expense = db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.type == "expense").scalar() or 0
    balance = total_income - total_expense
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    }

@router.get("/morosidad")
def get_morosidad(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin)):
    # Only Admin
    
    # Get all active users
    users = db.query(models.User).filter(models.User.is_active == True, models.User.role == 'partner').all()
    
    stats = []
    
    for user in users:
        # Get pending debts
        debts = db.query(models.Debt).filter(models.Debt.user_id == user.id, models.Debt.status == 'pending').all()
        
        # Calculate stats
        total_debt = sum(d.amount for d in debts)
        months_owed = [f"{d.month}/{str(d.year)[-2:]}" for d in debts] # Format 9/25
        
        # Heuristic for % (Arbitrary for now: max 6 months = 100%?)
        # Or relative to total assigned debts?
        # Let's count total debts generated for this user
        total_assigned = db.query(models.Debt).filter(models.Debt.user_id == user.id).count()
        unpaid_count = len(debts)
        
        percent = 0
        if total_assigned > 0:
            percent = int((unpaid_count / total_assigned) * 100)
        
        if total_debt > 0:
            stats.append({
                "user_name": user.nickname or user.name,
                "months_str": ", ".join(months_owed),
                "total_debt": total_debt,
                "percent": percent
            })
            
    return stats

@router.get("/reports/monthly")
def get_monthly_report(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Group by Year-Month
    try:
        results = db.query(
            func.extract('year', models.Transaction.date).label('year'),
            func.extract('month', models.Transaction.date).label('month'),
            models.Transaction.type,
            func.sum(models.Transaction.amount).label('total')
        ).group_by('year', 'month', models.Transaction.type).order_by('year', 'month').all()
        
        # Process into: labels: ["1/2026"], income: [100], expense: [50]
        data_map = {}
        for r in results:
            # r.year and r.month might be decimals/floats depending on DB driver, cast to int
            y = int(r.year)
            m = int(r.month)
            key = f"{m}/{y}"
            
            if key not in data_map:
                data_map[key] = {"income": 0, "expense": 0}
            
            if r.type == 'income':
                data_map[key]['income'] = float(r.total)
            elif r.type == 'expense':
                data_map[key]['expense'] = float(r.total)
        
        labels = list(data_map.keys())
        income = [data_map[k]['income'] for k in labels]
        expense = [data_map[k]['expense'] for k in labels]
        
        return {"labels": labels, "income": income, "expense": expense}
        
    except Exception as e:
        print(f"Error in monthly report: {e}")
        return {"labels": [], "income": [], "expense": []}

@router.get("/reports/categories")
def get_category_report(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    try:
        results = db.query(
            models.Transaction.category,
            func.sum(models.Transaction.amount).label('total')
        ).filter(models.Transaction.type == 'expense').group_by(models.Transaction.category).all()
        
        labels = [r.category or 'Otros' for r in results]
        data = [float(r.total) for r in results]
        
        return {"labels": labels, "data": data}
        
    except Exception as e:
        print(f"Error in category report: {e}")
        return {"labels": [], "data": []}

