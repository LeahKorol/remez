from apiflask import Schema
from apiflask.fields import String
from apiflask.validators import Length


class QueryIn(Schema):
    name = String(required=True, validate=Length(1, 10))
    text = String(required=True, validate=Length(1, 100))
