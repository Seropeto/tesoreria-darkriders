
import sqlalchemy
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@db/darkriders")

def fix_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            print("Checking schema...")
            # This is a rough check, or we just try to add it and ignore error
            conn.execute(text("ALTER TABLE transactions ADD COLUMN created_by_id INTEGER"))
            conn.execute(text("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_created_by FOREIGN KEY (created_by_id) REFERENCES users(id)"))
            print("Column created_by_id added successfully.")
        except Exception as e:
            print(f"Migration might have already run or failed: {e}")

if __name__ == "__main__":
    fix_schema()
