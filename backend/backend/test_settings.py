"""
This is a test settings file for Django. It overrides the default database settings.
You can a localinstalation of postgres or use docker: docker run --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
"""

import os

# Ensure FAERS bounds are set for tests.
os.environ.setdefault("FAERS_FROM", "2004q1")
os.environ.setdefault("FAERS_TO", "2025q4")

from backend.settings import *

# Use local Postgres database for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
