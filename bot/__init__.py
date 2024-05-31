import logging
import sys

from pyrogram import Client

from bot.database import DatabaseWrapper as Database
from bot.gemini import GeminiChat
from config import Config

logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y/%m/%d %H:%M:%S",
    format="[%(asctime)s][%(name)s][%(levelname)s] ==> %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)

Bot: Client = None
db: Database = None
gemini: GeminiChat
