import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from queries.models import Query  # Import your Django Query model

def get_query(query_id: int):
    try:
        return Query.objects.get(id=query_id)
    except Query.DoesNotExist:
        return None

def save_results(query_id: int, results: dict):
    query = get_query(query_id)
    if query:
        query.ror_values = results.get("ror_values", [])
        query.ror_lower = results.get("ror_lower", [])
        query.ror_upper = results.get("ror_upper", [])
        query.save()
        return True
    return False
