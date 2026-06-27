import os
import json
import glob
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from loguru import logger

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "medical_warehouse"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres123"),
}

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw" / "telegram_messages"
LOGS_DIR = BASE_DIR / "logs"

logger.add(
    LOGS_DIR / "loader_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    level="INFO"
)


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS raw;

            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                message_id      BIGINT,
                channel_name    VARCHAR(255),
                channel_title   VARCHAR(255),
                message_date    TIMESTAMP WITH TIME ZONE,
                message_text    TEXT,
                has_media       BOOLEAN,
                image_path      TEXT,
                views           INTEGER,
                forwards        INTEGER,
                scraped_at      TIMESTAMP WITH TIME ZONE,
                PRIMARY KEY (message_id, channel_name)
            );
        """)
        conn.commit()
        logger.info("Table raw.telegram_messages ready")


def load_json_files(conn):
    json_files = glob.glob(str(DATA_DIR / "**" / "*.json"), recursive=True)
    logger.info(f"Found {len(json_files)} JSON files to load")

    total_inserted = 0
    total_skipped = 0

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            messages = json.load(f)

        if not messages:
            continue

        rows = []
        for msg in messages:
            rows.append((
                msg.get("message_id"),
                msg.get("channel_name"),
                msg.get("channel_title"),
                msg.get("message_date"),
                msg.get("message_text", ""),
                msg.get("has_media", False),
                msg.get("image_path"),
                msg.get("views", 0),
                msg.get("forwards", 0),
                msg.get("scraped_at"),
            ))

        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO raw.telegram_messages (
                    message_id, channel_name, channel_title,
                    message_date, message_text, has_media,
                    image_path, views, forwards, scraped_at
                ) VALUES %s
                ON CONFLICT (message_id, channel_name) DO NOTHING
            """, rows)
            inserted = cur.rowcount
            conn.commit()

        total_inserted += inserted
        total_skipped += len(rows) - inserted
        logger.info(f"Loaded {json_file}: {inserted} inserted, {len(rows) - inserted} skipped")

    logger.info(f"Done. Total inserted: {total_inserted}, skipped: {total_skipped}")
    return total_inserted


def main():
    logger.info("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    logger.info("Connected!")

    create_table(conn)
    total = load_json_files(conn)
    conn.close()
    logger.info(f"Loading complete. {total} messages in warehouse.")


if __name__ == "__main__":
    main()