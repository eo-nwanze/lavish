import ssl
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class UnverifiedSSLBackend(EmailBackend):
    """
    Custom email backend that bypasses SSL certificate verification
    """
    def __init__(self, *args, **kwargs):
        # Create a custom SSL context that doesn't verify certificates
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        # Override any SSL context passed in with our unverified one
        kwargs['ssl_context'] = context
        
        logger.info("Using UnverifiedSSLBackend with SSL verification disabled")
        super().__init__(*args, **kwargs)
    
    def open(self):
        if self.connection:
            return False
        
        try:
            # Create a custom SSL context that doesn't verify certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            
            # Override the SSL context
            self.ssl_context = context
            
            # Call the parent method to open the connection
            logger.info("Opening SMTP connection with SSL verification disabled")
            return super().open()
        except Exception as e:
            logger.error(f"Error opening SMTP connection: {str(e)}")
            if not self.fail_silently:
                raise
            return False 