# Standard Library imports

# Core Flask imports
from apiflask import APIBlueprint

# Third-party imports

# App imports

bp = APIBlueprint("main", __name__)

from app.main import static_views
