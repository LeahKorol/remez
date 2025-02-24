# Standard Library imports

# Core Flask imports
from apiflask import APIBlueprint

# Third-party imports

# App imports

bp = APIBlueprint('api', __name__)

from app.api import auth, users