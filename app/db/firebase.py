# Standard Library imports

# Core Flask imports
from flask import Flask  # To access the app's current configuration

# Third-party imports
from firebase_admin import credentials, initialize_app, firestore
from google.cloud.firestore import Client

# App imports

class Firebase:
    _client: Client = None

    @classmethod
    def init_app(cls, app: Flask):
        """Initialize Firebase with the Flask app"""
        cred_path = app.config['FIREBASE_CREDENTIALS_PATH']
        cred = credentials.Certificate(cred_path)
        initialize_app(cred)
        cls._client = firestore.client()

    @classmethod
    def get_firestore(cls) -> Client:
        """Get the Firestore client"""
        if not cls._client:
            raise RuntimeError("Firebase not initialized. Call init_app() first.")
        return cls._client
