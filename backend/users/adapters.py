# from allauth.account.adapter import DefaultAccountAdapter
# from django.conf import settings
# import os

# class CustomAccountAdapter(DefaultAccountAdapter):
#     def get_email_confirmation_url(self, request, emailconfirmation):
#         backend_url = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000/api/v1/auth')
#         return f"{backend_url}/verify-email/{emailconfirmation.key}/"



from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
import os


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        backend_url = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
        return f"{backend_url}/api/v1/auth/verify-email/{emailconfirmation.key}/"
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Override to use custom email template
        """
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }
        
        # Use your custom template
        self.send_mail(
            "account/email/email_confirmation",
            emailconfirmation.email_address.email,
            ctx
        )