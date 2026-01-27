from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    nickname: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[datetime] = None

class UserCreate(UserBase):
    password: str
    role: str = "partner"

class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    nickname: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[datetime] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    role: str
    debts: List['Debt'] = [] # Forward Ref

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    amount: float
    type: str
    category: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    debt_ids: Optional[List[int]] = None # List of debts being paid by this transaction

class Transaction(TransactionBase):
    id: int
    date: datetime
    user: Optional['UserBase'] = None
    created_by: Optional['UserBase'] = None

    class Config:
        orm_mode = True

class DebtBase(BaseModel):
    month: int
    year: int
    amount: float
    user_id: int

class DebtCreate(DebtBase):
    pass

class Debt(DebtBase):
    id: int
    status: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
