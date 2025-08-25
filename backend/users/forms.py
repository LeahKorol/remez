from allauth.account.adapter import get_adapter
from allauth.account.forms import default_token_generator
from dj_rest_auth.forms import AllAuthPasswordResetForm
from allauth.account import app_settings
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from allauth.account.utils import (
    filter_users_by_email,
    user_username,
    user_pk_to_url_str,
)


class CustomAllAuthPasswordResetForm(AllAuthPasswordResetForm):
    """
    This class is based on this code:
    https://medium.com/%40etentuk/django-rest-framework-how-to-edit-reset-password-link-in-dj-rest-auth-with-dj-allauth-installed-c54bae36504e
    """

    def clean_email(self):
        """
        Invalid email should not raise error, as this would leak users
        for unit test: test_password_reset_with_invalid_email
        """
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)
        self.users = filter_users_by_email(email, is_active=True)
        return self.cleaned_data["email"]

    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in self.users:
            temp_key = token_generator.make_token(user)
            uid = user_pk_to_url_str(user)
            
            # create the URL that points to Django backend
            url = f"{settings.PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL}{user_pk_to_url_str(user)}/{temp_key}/"
            # Create the URL that points to React frontend
            frontend_base_url = getattr(settings, 'FRONTEND_PASSWORD_RESET_URL', 'http://localhost:3000/reset-password')
            reset_url = f"{frontend_base_url}/{uid}/{temp_key}/"
            

            # Values which are passed to password_reset_key_message.txt
            context = {
                "current_site": current_site,
                "user": user,
                "password_reset_url": reset_url, # This will be used in the email template
                "uid": uid, # available for direct use in template
                "token": temp_key, # available for direct use in template
            }

            if (
                app_settings.AUTHENTICATION_METHOD
                != app_settings.AuthenticationMethod.EMAIL
            ):
                context["username"] = user_username(user)
            get_adapter(request).send_mail(
                "account/email/password_reset_key", email, context
            )

        return self.cleaned_data["email"]
