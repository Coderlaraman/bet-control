import os
import sys
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine

def add_elo_columns():
    print("Adding Elo and Odds columns to fixtures table...")
    with engine.connect() as conn:
        columns = [
            ("home_elo", "FLOAT"),
            ("away_elo", "FLOAT"),
            ("home_odds", "FLOAT"),
            ("draw_odds", "FLOAT"),
            ("away_odds", "FLOAT")
        ]
        
        for col_name, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE fixtures ADD COLUMN {col_name} {col_type} NULL"))
                print(f"Added {col_name} column.")
            except ProgrammingError as e:
                print(f"Column {col_name} might already exist or error: {e}")
            
        conn.commit()
    print("Migration completed.")

if __name__ == "__main__":
    add_elo_columns()
