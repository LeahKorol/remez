# Standard Library imports

# Core Flask imports
from flask import session, jsonify, current_app

# Third-party imports
from firebase_admin import exceptions

# App imports
from app.api import bp
from app.decorators import auth_required
from app.utils.validate import QueryIn
from app.services import firestore_service as fs


@bp.post("/users/<string:uid>/queries")
@auth_required
@bp.input(QueryIn)
def create_query(uid: str, json_data):
    """Creates a new query for the authenticated user."""

    # Ensure user is modifying their own data
    if uid != session["user"]["uid"]:
        return (
            jsonify({"error": "Forbidden: Cannot create queries for other users"}),
            403,
        )
    # Parse incoming JSON data
    name = json_data["name"]
    text = json_data["text"]

    try:
        query_id = fs.create_query(uid, name, text)
        return jsonify({"query_id": query_id}), 201

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Query creation failed: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

    except Exception as e:
        current_app.logger.error(f"An error occured: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500
