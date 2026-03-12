from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas

from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    result = pwd_context.verify(plain_password, hashed_password)
    print(f"DEBUG: verify_password result={result}", flush=True)
    return result

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        role=user.role,
        nickname=user.nickname,
        phone_number=user.phone_number,
        birth_date=user.birth_date
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

    if user:
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
    return user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_transaction(db: Session, transaction: schemas.TransactionCreate, creator_id: int, commit: bool = True):
    # Sanitize payload
    tx_data = transaction.dict(exclude_unset=True)
    tx_data.pop('debt_ids', None)
    
    # Valid columns
    valid_cols = {'amount', 'type', 'category', 'description', 'user_id', 'date'}
    filtered_data = {k: v for k, v in tx_data.items() if k in valid_cols}
    
    db_transaction = models.Transaction(**filtered_data)
    db_transaction.created_by_id = creator_id
    
    # user_id handling:
    # If the payload has user_id, it is used (e.g. income from Partner).
    # If not, it remains None (external income/expense).
        
    db.add(db_transaction)
    if commit:
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def get_users(db: Session, skip: int = 0, limit: int = 100, role: str = None):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    return query.offset(skip).limit(limit).all()

def create_debt_bulk(db: Session, month: int, year: int, amount: float):
    # Get all active partners
    partners = db.query(models.User).filter(models.User.role == 'partner', models.User.is_active == True).all()
    created_count = 0
    for partner in partners:
        # Check if exists
        exists = db.query(models.Debt).filter(models.Debt.user_id == partner.id, models.Debt.month == month, models.Debt.year == year).first()
        if not exists:
            debt = models.Debt(month=month, year=year, amount=amount, user_id=partner.id, status="pending")
            db.add(debt)
            created_count += 1
    db.commit()
    return created_count

def get_pending_debts(db: Session, user_id: int = None):
    query = db.query(models.Debt).filter(models.Debt.status == "pending")
    if user_id:
        query = query.filter(models.Debt.user_id == user_id)
    return query.all()

def pay_debt(db: Session, debt_id: int, commit: bool = True):
    debt = db.query(models.Debt).filter(models.Debt.id == debt_id).first()
    if debt:
        debt.status = "paid"
        if commit:
            db.commit()
            db.refresh(debt)
    return debt
