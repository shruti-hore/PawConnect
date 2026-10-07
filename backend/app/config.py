import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths to allow loading .env regardless of working directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
backend_env = BACKEND_DIR / ".env"
root_env = BACKEND_DIR.parent / ".env"

if backend_env.is_file():
    load_dotenv(dotenv_path=backend_env)
elif root_env.is_file():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False