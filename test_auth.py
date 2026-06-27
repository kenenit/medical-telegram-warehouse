import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

print(f"Connecting with phone: {PHONE}")

with TelegramClient("medical_session", API_ID, API_HASH) as client:
    client.start(phone=PHONE)
    print("Successfully connected!")
    me = client.get_me()
    print(f"Logged in as: {me.first_name}")