from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

from .extensions import db, migrate

# Resolve backend and root directories for reliable .env loading
BACKEND_DIR = Path(__file__).resolve().parent.parent
backend_env = BACKEND_DIR / ".env"
root_env = BACKEND_DIR.parent / ".env"

if backend_env.is_file():
    load_dotenv(dotenv_path=backend_env)
elif root_env.is_file():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Validate that database configuration is present
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise ValueError(
            "DATABASE_URL is not set. Please ensure it is defined in backend/.env or your environment."
        )

    db.init_app(app)
    migrate.init_app(app, db, directory=str(BACKEND_DIR / "migrations"))

    # Register models with SQLAlchemy metadata
    from .models import (
        Role,
        User,
        NGO,
        Animal,
        RescueCase,
        AdoptionApplication,
        Donation,
        VolunteerApplication,
    )

    @app.get("/api/health")
    def health_check():
        return {
            "status": "success",
            "message": "PawConnect backend is running"
        }, 200

    return app