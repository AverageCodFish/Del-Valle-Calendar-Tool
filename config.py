import os
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment variables

class Config:
    try:
        DB_HOST = os.getenv("DB_HOST")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_NAME = os.getenv("DB_NAME")
    except Exception as e:
        raise RuntimeError("Failed to load database configuration from environment variables") from e
