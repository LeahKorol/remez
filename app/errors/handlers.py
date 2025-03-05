# Standard Library imports

# Core Flask imports
from flask import render_template, request
from apiflask.exceptions import HTTPError

# Third-party imports
from werkzeug.exceptions import HTTPException

# App imports
from app.errors import bp


def wants_json_response():
    # Check if the request was sent to our API
    return request.path.startswith("/api/")


def json_error_response(error):
    payload = {}
    code = getattr(error, "code", 500)

    if isinstance(error, HTTPError):
        # This is an APIFLask error that the api explicitly raised
        payload["message"] = error.get("message", "")
        payload["detail"] = error.get("detail", {})
    elif isinstance(error, HTTPException):
        # This is a Flask/Werkzeug error like 404 or 500
        payload["message"] = error.description or ""
        payload["detail"] = getattr(error, "data", {})
    else:
        # Some unknown/unexpected exception
        payload["message"] = "Internal server error"
        payload["detail"] = {}

    return payload, code


def html_error_response(error: HTTPException | HTTPError, template: str):
    # assign error code according to error type
    if isinstance(error, HTTPError):
        error_code = error.status_code
    else:
        error_code = getattr(error, "code", 500)

    return render_template(template), error_code


def handle_error_response(error: HTTPException | HTTPError, template: str):
    if wants_json_response():
        return json_error_response(error)
    return html_error_response(error, template)


@bp.app_errorhandler(404)
def not_found_error(error: HTTPException | HTTPError):
    return handle_error_response(error, "errors/404.html")


@bp.app_errorhandler(500)
def internal_error(error: HTTPException | HTTPError):
    return handle_error_response(error, "errors/500.html")


@bp.app_errorhandler(HTTPException)
def werkzeug_error(error: HTTPException):
    if wants_json_response():
        return json_error_response(error)
    return error
