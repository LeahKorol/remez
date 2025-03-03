# Standard Library imports

# Core Flask imports
from flask import current_app
from flask.views import MethodView
from apiflask import abort

# Third-party imports
from firebase_admin import exceptions

# App imports
from app.api import bp
from app.schemas import QueryIn, QueryOut
from app.utils.decorators import auth_required, restrict_user
from app.services import firestore_service as fs


class Query(MethodView):
    decorators = [restrict_user, auth_required, bp.doc(security="FirebaseSessionAuth")]

    @bp.output(QueryOut)
    def get(self, uid: str, query_id: str):
        try:
            query = fs.get_user_query(uid, query_id)
            if query:
                return query
            abort(404, message="Query not found")

        except exceptions.FirebaseError as e:
            current_app.logger.error(f"Query Retrieval failed: {e}")
            abort(500, message="Internal Server Error")

    @bp.output({}, status_code=204)
    def delete(self, uid: str, query_id: str):
        try:
            deleted_query = fs.delete_user_query(uid, query_id)
            if deleted_query:
                return ""
            abort(404, message="Query not found")

        except exceptions.FirebaseError as e:
            current_app.logger.error(f"Query Deletion failed: {e}")
            abort(500, message="Internal Server Error")

    @bp.input(QueryIn(partial=True))
    @bp.output(QueryOut)
    def patch(self, uid: str, query_id: str, json_data):
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


class Queries(MethodView):
    decorators = [restrict_user, auth_required, bp.doc(security="FirebaseSessionAuth")]

    @bp.input(QueryIn)
    @bp.output(QueryOut, status_code=201)
    def post(self, uid: str, json_data):
        # Parse incoming JSON data
        name = json_data["name"]
        text = json_data["text"]

        try:
            new_query = fs.create_user_query(uid, name, text)
            return new_query

        except exceptions.FirebaseError as e:
            current_app.logger.error(f"Query creation failed: {e}")
            abort(500, message="Internal Server Error")

    @bp.output(QueryOut(many=True))
    def get(self, uid: str):
        try:
            queries = fs.get_user_queries(uid)
            if queries:
                return queries
            abort(404, message="Queries not found")

        except exceptions.FirebaseError as e:
            current_app.logger.error(f"Queries Retrival failed: {e}")
            abort(500, message="Internal Server Error")


# assign the view
query_view = Query.as_view("query")
queries_view = Queries.as_view("queries")

bp.add_url_rule(
    "/users/<string:uid>/queries/<string:query_id>",
    view_func=query_view,
    methods=["GET", "DELETE", "PATCH"],
)

bp.add_url_rule(
    "/users/<string:uid>/queries",
    view_func=queries_view,
    methods=["GET", "POST"],
)
