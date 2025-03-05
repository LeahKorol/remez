# Standard Library imports
from typing import Optional

# Core Flask imports
from flask import request, current_app

# Third-party imports
from firebase_admin import auth
from werkzeug.exceptions import Unauthorized

# App imports


def verify_token() -> Optional[dict]:
    """
    Verifies the Firebase session token.

    Returns:
        dict: The authenticated user details if the token is valid.

    Raises:
        HTTP 401 (Unauthorized) if the token is missing or invalid.
        HTTP 500 (Internal Server Error) for unexpected issues.
    """
    session_cookie = request.cookies.get("session")

    if not session_cookie:
        current_app.logger.warning("Unauthorized: Missing session cookie.")
        raise Unauthorized(description="Unauthorized: Missing session cookie")

    try:
        # Verify the session cookie. If `check_revoked=True`, additional checks ensure the
        # user's session hasn't been revoked (e.g., user logged out, disabled, or deleted).
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=False)
        return decoded_claims  # Return the authenticated user details.

    except auth.InvalidSessionCookieError as e:
        current_app.logger.warning(
            f"Unauthorized: Invalid session cookie. Error: {str(e)}"
        )
        raise Unauthorized(description="Unauthorized: Invalid session cookie")

    except auth.AuthError as e:  # Catches broader Firebase authentication errors
        current_app.logger.error(f"Firebase AuthError: {str(e)}")
        raise Unauthorized(description="Unauthorized: Firebase authentication error")

    except Exception as e:
        current_app.logger.error(f"Unexpected error in verify_token: {e}")
        raise Unauthorized(description="Internal Server Error")
