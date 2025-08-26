from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
import os

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        backend_url = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000/api/v1/auth')
        return f"{backend_url}/verify-email/{emailconfirmation.key}/"
