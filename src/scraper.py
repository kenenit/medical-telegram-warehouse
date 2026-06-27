import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from loguru import logger

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

CHANNELS = [
    "CheMed123",
    "lobelia4cosmetics",
    "tikvahpharma",
]

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
IMAGES_DIR = DATA_DIR / "images"
MESSAGES_DIR = DATA_DIR / "telegram_messages"
LOGS_DIR = BASE_DIR / "logs"

LOGS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
MESSAGES_DIR.mkdir(parents=True, exist_ok=True)

logger.add(
    LOGS_DIR / "scraper_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


async def scrape_channel(client, channel_username):
    logger.info(f"Starting scrape: {channel_username}")
    messages_data = []
    today = datetime.now().strftime("%Y-%m-%d")

    image_dir = IMAGES_DIR / channel_username
    image_dir.mkdir(parents=True, exist_ok=True)

    try:
        entity = await client.get_entity(channel_username)
        channel_name = entity.title
        logger.info(f"Connected to: {channel_name}")

        async for message in client.iter_messages(entity, limit=500):
            has_media = False
            image_path = None

            if message.media and isinstance(message.media, MessageMediaPhoto):
                has_media = True
                image_filename = f"{message.id}.jpg"
                image_path = str(image_dir / image_filename)
                try:
                    await client.download_media(message.media, image_path)
                    logger.info(f"Downloaded image: {image_filename}")
                except Exception as e:
                    logger.error(f"Failed to download image {message.id}: {e}")
                    image_path = None

            message_data = {
                "message_id": message.id,
                "channel_name": channel_username,
                "channel_title": channel_name,
                "message_date": message.date.isoformat() if message.date else None,
                "message_text": message.text or "",
                "has_media": has_media,
                "image_path": image_path,
                "views": message.views or 0,
                "forwards": message.forwards or 0,
                "scraped_at": datetime.now().isoformat(),
            }
            messages_data.append(message_data)

        output_dir = MESSAGES_DIR / today
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{channel_username}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(messages_data)} messages from {channel_username}")
        return messages_data

    except Exception as e:
        logger.error(f"Failed to scrape {channel_username}: {e}")
        return []


async def main():
    logger.info("Starting Telegram scraper")

    async with TelegramClient("medical_session", API_ID, API_HASH) as client:
        await client.start(phone=PHONE)
        logger.info("Telegram client connected")

        all_data = {}
        for channel in CHANNELS:
            data = await scrape_channel(client, channel)
            all_data[channel] = len(data)
            await asyncio.sleep(2)

        logger.info(f"Scraping complete. Summary: {all_data}")


if __name__ == "__main__":
    asyncio.run(main())