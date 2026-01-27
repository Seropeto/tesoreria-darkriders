import sys
import os

# Ensure backend dir is in path
sys.path.append(os.getcwd())

import database, models
from sqlalchemy.orm import Session

def check_system_state():
    db = database.SessionLocal()
    
    print("\n--- ACTORS (USERS) ---")
    users = db.query(models.User).all()
    target_user_id = None
    for u in users:
        print(f"[ID: {u.id}] Name: '{u.name}' | Email: '{u.email}' | Role: '{u.role}' | Active: {u.is_active}")
        if "milla" in u.email.lower() or "milla" in u.name.lower():
            target_user_id = u.id

    print("\n--- DEBTS (All) ---")
    debts = db.query(models.Debt).all()
    for d in debts:
        status_icon = "PAID" if d.status == 'paid' else "PENDING"
        print(f"[Debt ID: {d.id}] UserID: {d.user_id} | {d.month}/{d.year} | ${d.amount} | {status_icon}")

    if target_user_id:
        print(f"\n--- DIAGNOSIS FOR FRANCISCO (ID: {target_user_id}) ---")
        user_debts = [d for d in debts if d.user_id == target_user_id]
        if not user_debts:
            print("(!) NO DEBTS FOUND FOR THIS USER.")
        else:
            for fd in user_debts:
                print(f" > Found debt: {fd.month}/{fd.year} - Status: {fd.status}")
    else:
        print("\n(!) FRANCISCO MILLA NOT FOUND IN USERS.")

    db.close()

if __name__ == "__main__":
    check_system_state()
