# Standard Library imports
from functools import wraps

# Core Flask imports
from flask import g
from flask.views import MethodView
from apiflask import abort

# Third-party imports

# App imports
from app.services.auth_service import verify_token


def auth_required(func):
    """
    Decorator that ensures authentication is required before accessing a route.
    - Verifies the Firebase session token.
    - Stores the authenticated user details in `g.current_user`.
    - Calls the original function if authentication succeeds.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        decoded_claims = verify_token()
        g.current_user = decoded_claims

        return func(*args, **kwargs)

    return wrapper


def restrict_user(func):
    """
    A decorator that ensures users can only access their own data.

    - Assumes authentication has already occurred (`@auth_required` should be used first).
    - Checks if the `uid` in the route matches the `current_user`'s UID.
    - If the user is trying to access another user's data, it raises a 403 error.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Decorator that ensures users can only access their own data."""
        # Ensure this decorator occurs after auth_required
        # print(f"Restrict User Check: g.current_user = {g.get('current_user', 'Not set')}")

        if not hasattr(g, "current_user"):
            abort(401, message="Unauthorized: Authentication is required")

        # Extract `uid` from args or kwargs
        uid = kwargs.get("uid", args[0] if args else None)

        if uid and uid != g.current_user["uid"]:
            abort(403, message="Forbidden: Cannot access other users' data")

        return func(*args, **kwargs)

    return wrapper
