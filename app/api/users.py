# Standard Library imports

# Core Flask imports
from flask import session, current_app
from apiflask import abort

# Third-party imports
from firebase_admin import exceptions

# App imports
from app.api import bp
from app.decorators import auth_required
from app.utils.validate import QueryIn, QueryOut
from app.services import firestore_service as fs


def check_user_permission(uid):
    """Ensure the user is accessing their own data."""
    if uid != session.get("user", {}).get("uid"):
        return {"message": "Forbidden: Cannot access other users data"}, 403
    return None  # Return None when the check passes


@bp.post("/users/<string:uid>/queries")
@auth_required
@bp.input(QueryIn)
@bp.output(QueryOut, status_code=201)
def create_query(uid: str, json_data):
    # Ensure user is modifying their own data
    response = check_user_permission(uid)
    if response:
        return response

    # Parse incoming JSON data
    name = json_data["name"]
    text = json_data["text"]

    try:
        new_query = fs.create_user_query(uid, name, text)
        return new_query

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Query creation failed: {e}")
        abort(500, message="Internal Server Error")

    except Exception as e:
        current_app.logger.error(f"An error occured: {e}")
        abort(500, message="Internal Server Error")


@bp.get("/users/<string:uid>/queries/<string:query_id>")
@auth_required
@bp.output(QueryOut)
def get_query(uid: str, query_id: str):
    # Ensure user is modifying their own data
    response = check_user_permission(uid)
    if response:
        return response
    try:
        query = fs.get_user_query(uid, query_id)
        if query:
            return query
        abort(404, message="Query not found")

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Query Retrival failed: {e}")
        abort(500, message="Internal Server Error")

    except Exception as e:
        current_app.logger.error(f"An error occured: {e}")
        abort(500, message="Internal Server Error")


@bp.get("/users/<string:uid>/queries")
@auth_required
@bp.output(QueryOut(many=True))
def get_queries(uid: str):
    # Ensure user is modifying their own data
    response = check_user_permission(uid)
    if response:
        return response
    try:
        queries = fs.get_user_queries(uid)
        if queries:
            return queries
        abort(404, message="Queries not found")

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Queries Retrival failed: {e}")
        abort(500, message="Internal Server Error")

    except Exception as e:
        current_app.logger.error(f"An error occured: {e}")
        abort(500, message="Internal Server Error")


@bp.patch("/users/<string:uid>/queries/<string:query_id>")
@auth_required
@bp.input(QueryIn(partial=True))
@bp.output(QueryOut)
def update_query(uid: str, query_id: str, json_data):
    # Ensure user is modifying their own data
    response = check_user_permission(uid)
    if response:
        return response

    # Parse incoming JSON data
    name = json_data.get("name", None)
    text = json_data.get("text", None)

    try:
        updated_query = fs.update_user_query(uid, query_id, name, text)
        if updated_query:
            return updated_query
        abort(404, message="Query not found")

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Queriy's update failed: {e}")
        abort(500, message="Internal Server Error")

    except Exception as e:
        current_app.logger.error(f"An error occured: {e}")
        abort(500, message="Internal Server Error")


@bp.delete("/users/<string:uid>/queries/<string:query_id>")
@auth_required
@bp.output({}, status_code=204)
def delete_query(uid: str, query_id: str):
    # Ensure user is modifying their own data
    response = check_user_permission(uid)
    if response:
        return response
    try:
        deleted_query = fs.delete_user_query(uid, query_id)
        if deleted_query:
            return ""
        abort(404, message="Query not found")

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Query Deletion failed: {e}")
        abort(500, message="Internal Server Error")

    except Exception as e:
        current_app.logger.error(f"An error occured: {e}")
        abort(500, message="Internal Server Error")
