import os

from dotenv import load_dotenv

load_dotenv()


class Config(object):
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///geminibot.db")