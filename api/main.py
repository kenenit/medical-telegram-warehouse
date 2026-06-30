from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from api.database import get_db
from api import schemas

app = FastAPI(
    title="Ethiopian Medical Telegram API",
    description="Analytical API for Ethiopian medical Telegram channel data",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Ethiopian Medical Telegram Warehouse API", "status": "running"}


@app.get("/api/reports/top-products", response_model=List[schemas.TopProduct])
def top_products(limit: int = 10, db: Session = Depends(get_db)):
    """Returns the most frequently mentioned terms across all channels."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    query = text("""
        SELECT word AS term, COUNT(*) as count
        FROM (
            SELECT regexp_split_to_table(
                lower(message_text), '\s+'
            ) AS word
            FROM public.stg_telegram_messages
            WHERE length(message_text) > 0
        ) words
        WHERE length(word) > 4
          AND word NOT IN ('with','this','that','from','have','will',
                           'your','been','they','were','when','what',
                           'about','which','there','their','these')
        GROUP BY word
        ORDER BY count DESC
        LIMIT :limit
    """)
    try:
        rows = db.execute(query, {"limit": limit}).fetchall()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

    return [{"term": row[0], "count": row[1]} for row in rows]


@app.get("/api/channels/{channel_name}/activity", response_model=schemas.ChannelActivity)
def channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """Returns posting activity and trends for a specific channel."""
    if not channel_name or not channel_name.strip():
        raise HTTPException(status_code=400, detail="channel_name cannot be empty")

    query = text("""
        SELECT
            channel_name,
            channel_title,
            channel_type,
            total_posts,
            avg_views,
            first_post_date::text,
            last_post_date::text
        FROM public.dim_channels
        WHERE lower(channel_name) = lower(:channel_name)
    """)
    try:
        row = db.execute(query, {"channel_name": channel_name}).fetchone()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

    if not row:
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")

    return {
        "channel_name": row[0],
        "channel_title": row[1],
        "channel_type": row[2],
        "total_posts": row[3],
        "avg_views": float(row[4]) if row[4] is not None else 0.0,
        "first_post_date": row[5],
        "last_post_date": row[6],
    }


@app.get("/api/search/messages", response_model=List[schemas.MessageResult])
def search_messages(query: str, limit: int = 20, db: Session = Depends(get_db)):
    """Searches for messages containing a specific keyword."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="query parameter cannot be empty")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    sql = text("""
        SELECT
            message_id,
            channel_name,
            message_text,
            views,
            forwards,
            has_image
        FROM public.stg_telegram_messages
        WHERE lower(message_text) LIKE lower(:query)
        ORDER BY views DESC
        LIMIT :limit
    """)
    try:
        rows = db.execute(sql, {"query": f"%{query}%", "limit": limit}).fetchall()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

    return [
        {
            "message_id": row[0],
            "channel_name": row[1],
            "message_text": row[2],
            "views": row[3],
            "forwards": row[4],
            "has_image": row[5],
        }
        for row in rows
    ]


@app.get("/api/reports/visual-content", response_model=List[schemas.VisualContentStat])
def visual_content(db: Session = Depends(get_db)):
    """Returns statistics about image usage across channels."""
    query = text("""
        SELECT
            channel_name,
            COUNT(*) as total_images,
            SUM(CASE WHEN image_category = 'promotional' THEN 1 ELSE 0 END) as promotional,
            SUM(CASE WHEN image_category = 'product_display' THEN 1 ELSE 0 END) as product_display,
            SUM(CASE WHEN image_category = 'lifestyle' THEN 1 ELSE 0 END) as lifestyle,
            SUM(CASE WHEN image_category = 'other' THEN 1 ELSE 0 END) as other
        FROM public.fct_image_detections
        GROUP BY channel_name
        ORDER BY total_images DESC
    """)
    try:
        rows = db.execute(query).fetchall()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

    return [
        {
            "channel_name": row[0],
            "total_images": row[1],
            "promotional": row[2],
            "product_display": row[3],
            "lifestyle": row[4],
            "other": row[5],
        }
        for row in rows
    ]