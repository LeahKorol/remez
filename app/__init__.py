# Standard Library imports
import logging
from logging.handlers import RotatingFileHandler
import os

# Core Flask imports
from apiflask import APIFlask

# Third-party imports

# App imports
from config import config_manager
from app.db.firebase import Firebase


def load_logs(app: APIFlask) -> None:
    """Initialize a logging stream for the app."""

    # Create a formatter for consistency
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
    if app.config["LOG_TO_STDOUT"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        app.logger.addHandler(stream_handler)
    else:
        # Ensure the logs directory exists
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240, backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    # Handle messages at the INFO level and above
    app.logger.setLevel(logging.INFO)
    # first message
    app.logger.info("app startup")


def create_app(config_name):
    app = APIFlask(__name__)
    app.config.from_object(config_manager[config_name])

    # Firebase Admin SDK setup
    Firebase.init_app(app)

    from app.main import bp as views_bp

    app.register_blueprint(views_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    if not app.debug and not app.testing:
        load_logs(app)

    # with app.app_context():
    #     print(app.url_map)

    return app
