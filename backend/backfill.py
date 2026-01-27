
import sqlalchemy
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@db/darkriders")

def backfill():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Find an admin user
            result = conn.execute(text("SELECT id FROM users WHERE role='admin' LIMIT 1"))
            admin = result.fetchone()
            if admin:
                admin_id = admin[0]
                # Update nulls
                r = conn.execute(text(f"UPDATE transactions SET created_by_id = {admin_id} WHERE created_by_id IS NULL"))
                conn.commit()
                print(f"SUCCESS: Backfilled {r.rowcount} rows with admin id {admin_id}")
            else:
                print("ERROR: No admin found")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    backfill()
