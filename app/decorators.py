# Standard Library imports

# Core Flask imports
from functools import wraps
from flask import session, redirect, url_for

# Third-party imports

# App imports

# Decorator for routes that require authentication
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if 'user' not in session:
            return redirect(url_for('main.login'))
        else:
            return f(*args, **kwargs)

    return decorated_function