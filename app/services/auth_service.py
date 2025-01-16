# Standard Library imports

# Core Flask imports

# Third-party imports
from firebase_admin import auth

# App imports

def verify_token(token):
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")
