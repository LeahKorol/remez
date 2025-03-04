# Standard Library imports

# Core Flask imports
from flask import render_template, request
from apiflask import abort

# Third-party imports
from werkzeug.exceptions import HTTPException

# App imports
from app.errors import bp


def wants_json_response():
    return (
        request.accept_mimetypes["application/json"]
        >= request.accept_mimetypes["text/html"]
    )


def handle_error_response(error: HTTPException, template: str):
    if wants_json_response():
        return abort(error.code)
    return render_template(template), error.code


@bp.app_errorhandler(404)
def not_found_error(error: HTTPException):
    return handle_error_response(error, "errors/404.html")


@bp.app_errorhandler(500)
def internal_error(error: HTTPException):
    return handle_error_response(error, "errors/500.html")
