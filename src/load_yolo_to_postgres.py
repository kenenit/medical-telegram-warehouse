import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from loguru import logger

load_dotenv()

HOST = os.getenv("POSTGRES_HOST", "172.31.32.97")
PORT = os.getenv("POSTGRES_PORT", "5432")
DB = os.getenv("POSTGRES_DB", "medical_warehouse")
USER = os.getenv("POSTGRES_USER", "postgres")
PASS = os.getenv("POSTGRES_PASSWORD", "x")

BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "data" / "yolo_detections.csv"

engine = create_engine(f"postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}")


def load_yolo_results():
    logger.info("Loading YOLO results into PostgreSQL...")

    df = pd.read_csv(CSV_FILE)
    logger.info(f"Loaded {len(df)} rows from CSV")

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.execute(text("""
            DROP TABLE IF EXISTS raw.yolo_detections;
            CREATE TABLE raw.yolo_detections (
                message_id      VARCHAR(50),
                channel_name    VARCHAR(255),
                image_path      TEXT,
                detected_class  VARCHAR(100),
                confidence_score FLOAT,
                image_category  VARCHAR(50)
            );
        """))
        conn.commit()

    df.to_sql(
        "yolo_detections",
        engine,
        schema="raw",
        if_exists="append",
        index=False
    )

    logger.info("YOLO results loaded successfully!")


if __name__ == "__main__":
    load_yolo_results()