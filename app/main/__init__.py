# Standard Library imports

# Core Flask imports
from flask import Blueprint

# Third-party imports

# App imports

bp = Blueprint('main', __name__)

from app.main import static_views


