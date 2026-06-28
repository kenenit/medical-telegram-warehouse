import subprocess
import os
from pathlib import Path
from dagster import op, job, ScheduleDefinition, DefaultScheduleStatus, Definitions

BASE_DIR = Path(__file__).parent


@op
def scrape_telegram_data(context):
    context.log.info("Starting Telegram scraping...")
    result = subprocess.run(
        ["python", str(BASE_DIR / "src" / "scraper.py")],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Scraper failed: {result.stderr}")
    context.log.info("Scraping complete!")


@op
def load_raw_to_postgres(context):
    context.log.info("Loading raw data to PostgreSQL...")
    result = subprocess.run(
        ["python", str(BASE_DIR / "src" / "load_to_postgres.py")],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Loader failed: {result.stderr}")
    context.log.info("Loading complete!")


@op
def run_dbt_transformations(context):
    context.log.info("Running dbt transformations...")
    result = subprocess.run(
        ["dbt", "run"],
        capture_output=True, text=True,
        cwd=BASE_DIR / "medical_warehouse"
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt failed: {result.stderr}")

    test_result = subprocess.run(
        ["dbt", "test"],
        capture_output=True, text=True,
        cwd=BASE_DIR / "medical_warehouse"
    )
    context.log.info(test_result.stdout)
    context.log.info("dbt transformations complete!")


@op
def run_yolo_enrichment(context):
    context.log.info("Running YOLO object detection...")
    result = subprocess.run(
        ["python", str(BASE_DIR / "src" / "yolo_detect.py")],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"YOLO failed: {result.stderr}")

    load_result = subprocess.run(
        ["python", str(BASE_DIR / "src" / "load_yolo_to_postgres.py")],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    context.log.info(load_result.stdout)
    context.log.info("YOLO enrichment complete!")


@job
def medical_pipeline():
    raw_data = scrape_telegram_data()
    loaded = load_raw_to_postgres()
    transformed = run_dbt_transformations()
    enriched = run_yolo_enrichment()


daily_schedule = ScheduleDefinition(
    job=medical_pipeline,
    cron_schedule="0 6 * * *",
    default_status=DefaultScheduleStatus.RUNNING,
)

defs = Definitions(
    jobs=[medical_pipeline],
    schedules=[daily_schedule],
)