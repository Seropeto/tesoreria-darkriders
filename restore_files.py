
import os

files = {
    "/app/models.py": """from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime
import pytz

santiago_tz = pytz.timezone('America/Santiago')

def get_chile_time():
    return datetime.datetime.now(santiago_tz)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="partner")
    is_active = Column(Boolean, default=True)
    
    nickname = Column(String(100), nullable=True)
    phone_number = Column(String(50), nullable=True)
    birth_date = Column(DateTime, nullable=True)

    transactions = relationship("Transaction", foreign_keys="Transaction.user_id", back_populates="user")
    debts = relationship("Debt", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    date = Column(DateTime, default=get_chile_time)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    created_by = relationship("User", foreign_keys=[created_by_id])

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="debts")
""",
    "/app/schemas.py": """from typing import Optional, List
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
    debts: List['Debt'] = []

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    amount: float
    type: str
    category: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    debt_ids: Optional[List[int]] = None

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
"""
}

for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)
    print(f"Restored {path}")
