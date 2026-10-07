from flask import Flask
from dotenv import load_dotenv

from .extensions import db

load_dotenv()

from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    @app.get("/api/health")
    def health_check():
        return {
            "status": "success",
            "message": "PawConnect backend is running"
        }, 200

    return app