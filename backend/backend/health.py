import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Health check failed: database is unavailable.")
        return JsonResponse({"status": "error", "db": "error"}, status=503)

    return JsonResponse({"status": "ok", "db": "ok"})
