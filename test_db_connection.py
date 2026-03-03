from app.database import SessionLocal, engine
from sqlalchemy import text

def test_connection():
    print(f"Engine URL: {engine.url}")
    print(f"Pool size: {engine.pool.size()}")
    print(f"Max overflow: {engine.pool._max_overflow}")
    
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        print(f"Query Result: {result}")
        print("Success: Connected to PostgreSQL.")
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
