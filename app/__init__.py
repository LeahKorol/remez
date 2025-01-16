from flask import Flask
from config import config_manager

from .firebase_init import FirebaseApp

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_manager[config_name])

    # Firebase Admin SDK setup
    FirebaseApp.init_app(app)

    from .main import bp as views_bp
    app.register_blueprint(views_bp)

    from .api import bp as api_bp
    app.register_blueprint(api_bp)

    return app