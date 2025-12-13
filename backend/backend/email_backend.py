"""
Custom SMTP email backend for Python 3.13 compatibility.
Handles stricter SSL certificate validation in Python 3.13+.
"""
import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class Python313EmailBackend(SMTPBackend):
    """
    SMTP backend that uses unverified SSL context for Python 3.13+.
    This is the standard workaround for development environments with SSL certificate issues.
    """
    
    def open(self):
        """
        Ensure connection uses unverified SSL context for STARTTLS.
        """
        if self.connection:
            return False
        
        connection_params = {'timeout': self.timeout} if self.timeout is not None else {}
        
        try:
            self.connection = self.connection_class(self.host, self.port, **connection_params)
            
            if self.use_tls:
                self.connection.ehlo()
                # Use unverified context for STARTTLS - this is the fix for Python 3.13
                context = ssl._create_unverified_context()
                self.connection.starttls(context=context)
                self.connection.ehlo()
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except Exception:
            if not self.fail_silently:
                raise
