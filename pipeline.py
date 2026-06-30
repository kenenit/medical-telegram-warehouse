import subprocess
import os
from pathlib import Path
from dagster import op, job, ScheduleDefinition, DefaultScheduleStatus, Definitions, Failure

BASE_DIR = Path(__file__).parent


def run_subprocess(context, command, cwd, step_name):
    """Run a subprocess and raise a Dagster Failure with details on error."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=cwd, timeout=1800
        )
    except subprocess.TimeoutExpired:
        raise Failure(f"{step_name} timed out after 30 minutes")
    except FileNotFoundError as e:
        raise Failure(f"{step_name} failed: command not found — {e}")

    context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)

    if result.returncode != 0:
        raise Failure(
            description=f"{step_name} failed with exit code {result.returncode}",
            metadata={"stderr": result.stderr[-2000:] if result.stderr else "No stderr"}
        )
    return result


@op
def scrape_telegram_data(context):
    context.log.info("Starting Telegram scraping...")
    run_subprocess(
        context,
        ["python", str(BASE_DIR / "src" / "scraper.py")],
        BASE_DIR,
        "Telegram scraper"
    )
    context.log.info("Scraping complete!")


@op
def load_raw_to_postgres(context):
    context.log.info("Loading raw data to PostgreSQL...")
    run_subprocess(
        context,
        ["python", str(BASE_DIR / "src" / "load_to_postgres.py")],
        BASE_DIR,
        "PostgreSQL loader"
    )
    context.log.info("Loading complete!")


@op
def run_dbt_transformations(context):
    context.log.info("Running dbt transformations...")
    run_subprocess(
        context,
        ["dbt", "run"],
        BASE_DIR / "medical_warehouse",
        "dbt run"
    )
    run_subprocess(
        context,
        ["dbt", "test"],
        BASE_DIR / "medical_warehouse",
        "dbt test"
    )
    context.log.info("dbt transformations complete!")


@op
def run_yolo_enrichment(context):
    context.log.info("Running YOLO object detection...")
    run_subprocess(
        context,
        ["python", str(BASE_DIR / "src" / "yolo_detect.py")],
        BASE_DIR,
        "YOLO detector"
    )
    run_subprocess(
        context,
        ["python", str(BASE_DIR / "src" / "load_yolo_to_postgres.py")],
        BASE_DIR,
        "YOLO results loader"
    )
    context.log.info("YOLO enrichment complete!")


@job
def medical_pipeline():
    scrape_telegram_data()
    load_raw_to_postgres()
    run_dbt_transformations()
    run_yolo_enrichment()


daily_schedule = ScheduleDefinition(
    job=medical_pipeline,
    cron_schedule="0 6 * * *",
    default_status=DefaultScheduleStatus.RUNNING,
)

defs = Definitions(
    jobs=[medical_pipeline],
    schedules=[daily_schedule],
)