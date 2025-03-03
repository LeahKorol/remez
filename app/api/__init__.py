# Standard Library imports

# Core Flask imports
from apiflask import APIBlueprint

# Third-party imports

# App imports

bp = APIBlueprint("api", __name__)

# Import route modules AFTER defining `bp`
from app.api import auth, users
