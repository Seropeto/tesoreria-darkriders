from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime
import pytz

# Timezone
santiago_tz = pytz.timezone('America/Santiago')

def get_chile_time():
    return datetime.datetime.now(santiago_tz)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="partner") # 'admin', 'partner'
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
    type = Column(String(50), nullable=False) # 'income', 'expense'
    category = Column(String(100), nullable=True) # 'quota', 'other' for income; 'rent', etc for expense
    description = Column(String(255), nullable=True)
    date = Column(DateTime, default=get_chile_time)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Linked User (if income from partner)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Admin who created it

    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    created_by = relationship("User", foreign_keys=[created_by_id])

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending") # 'pending', 'paid'
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="debts")
