import django
from dotenv import load_dotenv


def setup_django_environemnt():
    """
    Setup Django environment & environemt variables for multiprocessing tasks.
    It's required because on Windows, new processes are spawned rather than forked.
    """
    load_dotenv()
    django.setup()
