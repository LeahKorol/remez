import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.EMAIL_HOST
        self.smtp_port = settings.EMAIL_PORT
        self.email_user = settings.EMAIL_HOST_USER
        self.email_password = settings.EMAIL_HOST_PASSWORD
        self.use_tls = settings.EMAIL_USE_TLS
        
    def send_query_completion_email(self, user_email, query_name, chart_url=None, chart_file_path=None):
        """
        Send email notification when query processing is complete
        """
        try:
            # Email subject
            subject = f"Your Query Analysis is Ready: {query_name}"
            
            # Email context for template
            context = {
                'query_name': query_name,
                'chart_url': chart_url,
                'user_email': user_email,
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'site_name': getattr(settings, 'SITE_NAME', 'Drug Analysis Platform')
            }
            
            # Render HTML email template
            html_content = render_to_string('account/email/email_query_completion.html', context)
            text_content = strip_tags(html_content)  # Plain text version
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Attach chart file if provided
            if chart_file_path and os.path.exists(chart_file_path):
                with open(chart_file_path, 'rb') as attachment:
                    email.attach(
                        f"{query_name}_chart.png", 
                        attachment.read(), 
                        'image/png'
                    )
            
            # Send email
            email.send()
            
            logger.info(f"Query completion email sent successfully to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {user_email}: {str(e)}")
            return False
    
    def send_query_error_email(self, user_email, query_name, error_message, chart_url=None):
        """
        Send email notification when query processing fails
        """
        try:
            subject = f"Query Processing Failed: {query_name}"
            
            context = {
                'query_name': query_name,
                'error_message': error_message,
                'user_email': user_email,
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'site_name': getattr(settings, 'SITE_NAME', 'Drug Analysis Platform'),
                'chart_url': chart_url  # if chart_url exists 
            }
            
            html_content = render_to_string('account/email/email_query_error.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Query error email sent successfully to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send error email to {user_email}: {str(e)}")
            return False
