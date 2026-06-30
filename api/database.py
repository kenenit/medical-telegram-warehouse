import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

load_dotenv()

HOST = os.getenv("POSTGRES_HOST", "172.31.32.97")
PORT = os.getenv("POSTGRES_PORT", "5432")
DB = os.getenv("POSTGRES_DB", "medical_warehouse")
USER = os.getenv("POSTGRES_USER", "postgres")
PASS = os.getenv("POSTGRES_PASSWORD", "x")

DATABASE_URL = f"postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        pass
except OperationalError as e:
    print(f"FATAL: Could not connect to PostgreSQL at {HOST}:{PORT}")
    print(f"Error: {e}")
    print("Hint: Run 'wsl hostname -I' and update POSTGRES_HOST in .env")
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        db.rollback()
        raise
    finally:
        db.close()