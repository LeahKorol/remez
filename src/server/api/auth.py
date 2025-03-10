# Standard Library imports

# Core Flask imports
from flask import current_app, jsonify
from apiflask import abort
from flask import g

# Third-party imports
from firebase_admin import auth, exceptions
import datetime
import time

# App imports
from app.api import bp
from app.schemas import Login, MeOut
from app.utils.decorators import auth_required


@bp.post("/sessionLogin")
@bp.input(Login)
def session_login(json_data):
    # Get the ID token sent by the client
    id_token = json_data["idToken"]

    # Set session cookies settings
    expires_in = current_app.config["PERMANENT_SESSION_LIFETIME"]
    httponly = current_app.config["SESSION_COOKIE_HTTPONLY"]
    secure = current_app.config["SESSION_COOKIE_SECURE"]

    try:
        decoded_claims = auth.verify_id_token(id_token)
        # Only process if the user signed in within the last 5 minutes.
        if time.time() - decoded_claims["auth_time"] < 5 * 60:
            # Create the session cookie. This will also verify the ID token in the process.
            # The session cookie will have the same claims as the ID token.
            session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
            response = jsonify({"status": "success"})

            # Set cookie policy for session cookie.
            expires = datetime.datetime.now() + expires_in
            response.set_cookie(
                "session",
                session_cookie,
                expires=expires,
                httponly=httponly,
                secure=secure,
            )
            return response

        # User did not sign in recently. To guard against ID token theft, require
        # re-authentication.
        abort(401, "Recent sign in required")
    except auth.InvalidIdTokenError:
        abort(401, "Invalid ID token")
    except exceptions.FirebaseError:
        abort(401, "Failed to create a session cookie")


@bp.post("/sessionLogout")
def session_logout():
    response = jsonify({"status": "success"})
    response.set_cookie("session", expires=0)
    return response


@bp.get("/me")
@auth_required
@bp.output(MeOut)
@bp.doc(security="FirebaseSessionAuth")
def get_user_details():
    return {"uid": g.current_user["uid"]}
