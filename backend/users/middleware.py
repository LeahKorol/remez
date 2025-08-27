import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate
from allauth.account.models import EmailAddress
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class EmailVerificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Only check for login endpoint
        if request.path.endswith('/login/') and request.method == 'POST':
            try:
                if hasattr(request, 'body') and request.body:
                    data = json.loads(request.body)
                    email = data.get('email', '')
                    password = data.get('password', '')
                    
                    if email and password:
                        try:
                            user = User.objects.get(email=email, is_active=True)
                            
                            # First authenticate - check if credentials are correct
                            auth_user = authenticate(username=email, password=password)
                            
                            if auth_user:  # Credentials are correct
                                # Now check if email is verified
                                unverified_email = EmailAddress.objects.filter(
                                    user=user,
                                    email=email,
                                    verified=False
                                ).first()
                                
                                if unverified_email:
                                    return JsonResponse({
                                        'error': 'email_not_verified',
                                        'detail': 'Your email is not verified yet. Please check your email and click the verification link.',
                                        'email': email
                                    }, status=403)
                                    
                        except User.DoesNotExist:
                            pass
                            
            except (json.JSONDecodeError, AttributeError):
                pass
                
        return None