import os
from dotenv import load_dotenv
from datetime import timedelta

# Loads environment variables from the .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

#  Config is a base class containing common configuration settings.
#  The other config classes inherit from it.
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Configure session cookie settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE') or True
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY') or True

    # Retrieve the number of days as a string and convert it to an integer
    permanent_session_lifetime_days = int(os.getenv('PERMANENT_SESSION_LIFETIME', 1))
    # Set the PERMANENT_SESSION_LIFETIME using timedelta
    PERMANENT_SESSION_LIFETIME = timedelta(days=permanent_session_lifetime_days)

    SESSION_REFRESH_EACH_REQUEST = os.environ.get('SESSION_REFRESH_EACH_REQUEST') or True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE') or 'Lax'

    # configurate path to firebase credentials
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')

class DevelopmentConfig(Config):
    pass


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass

config_manager = {
    "dev": DevelopmentConfig,
    "test": TestingConfig,
    "prod": ProductionConfig,
}
