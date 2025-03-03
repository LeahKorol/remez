# Standard Library imports

# Core Flask imports
from apiflask import Schema
from apiflask.fields import String
from apiflask.validators import Length

# Third-party imports

# App imports


class QueryIn(Schema):
    name = String(required=True, validate=Length(1, 50))
    text = String(required=True, validate=Length(1, 100))


class QueryOut(Schema):
    id = String()
    name = String()
    text = String()
    created_at = String()


class Login(Schema):
    idToken = String(required=True)
