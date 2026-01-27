from sqlalchemy.orm import Session
import models, database, crud

db = database.SessionLocal()
users = db.query(models.User).all()

print("--- USERS ---")
for u in users:
    print(f"ID: {u.id} | Name: {u.name} | Email: {u.email} | Role: {u.role} | Active: {u.is_active}")

print("\n--- DEBTS ---")
debts = db.query(models.Debt).all()
for d in debts:
    print(f"ID: {d.id} | UserID: {d.user_id} | Month: {d.month}/{d.year} | Amt: {d.amount} | Status: {d.status}")

db.close()
