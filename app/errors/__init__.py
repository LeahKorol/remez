# Standard Library imports

# Core Flask imports
from apiflask import APIBlueprint

# Third-party imports

# App imports

# Disable OpenAPI support for this blueprint since it is only responsible for formatting error responses.
bp = APIBlueprint("errors", __name__, enable_openapi=False)

from app.errors import handlers
