# Standard Library imports

# Core Flask imports
from flask import Flask

# Third-party imports

# App imports
from config import config_manager
from app.db.firebase import Firebase

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_manager[config_name])

    # Firebase Admin SDK setup
    Firebase.init_app(app)

    from app.main import bp as views_bp
    app.register_blueprint(views_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp)

    return app