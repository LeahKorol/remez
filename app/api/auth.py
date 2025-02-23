# Standard Library imports

# Core Flask imports
from flask import request, session, current_app

# Third-party imports

# App imports
from app.services import auth_service
from app.api import bp

@bp.route('/auth', methods=['POST'])
def authorize():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return {'message':'Unauthorized'}, 401

    token = token[7:]  # Strip off 'Bearer ' to get the actual token

    try:
        decoded_token = auth_service.verify_token(token)  # Validate token here
        session['user'] = decoded_token  # Add user to session
        return {'message':'Authorized'}, 200
    except ValueError as e:
        current_app.logger.error(f"Token verification failed: {e}")
        return {'message':'Unauthorized'}, 401