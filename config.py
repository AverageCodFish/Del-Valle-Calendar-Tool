import os
from dotenv import load_dotenv

# load .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:
    try:
        DB_HOST = os.getenv("DB_HOST")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_NAME = os.getenv("DB_NAME")
        APP_PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH")

        if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, APP_PASSWORD_HASH]):
            raise ValueError("One or more database configuration values are missing")
    except Exception as e:
        raise RuntimeError("Failed to load database configuration from environment variables") from e
