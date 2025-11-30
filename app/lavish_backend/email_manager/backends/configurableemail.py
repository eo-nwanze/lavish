import logging
import ssl
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend

logger = logging.getLogger(__name__)

class ConfigurableEmailBackend(EmailBackend):
    """
    A custom email backend that gets SMTP settings from the database and handles SSL verification.
    
    If no configuration is found in the database, it will fall back to
    the console backend in development mode (DEBUG=True) or use Django's
    default email settings.
    """

    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        
        # Import here to avoid circular imports
        from ..models import EmailConfiguration
        
        try:
            # Try to get the default configuration from the database
            config = EmailConfiguration.objects.filter(is_default=True).first()
            
            if config:
                logger.info(f"Using email configuration: {config.name}")
                
                # Use settings from the database
                host = config.email_host
                port = config.email_port
                username = config.email_host_user
                password = config.email_host_password
                use_tls = config.email_use_tls
                use_ssl = config.email_use_ssl
                timeout = getattr(settings, 'EMAIL_TIMEOUT', timeout)
                
                # Create a custom SSL context that disables certificate verification
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                
                # Call the parent init with these settings
                super().__init__(
                    host=host, port=port, username=username, password=password,
                    use_tls=use_tls, fail_silently=fail_silently, use_ssl=use_ssl,
                    timeout=timeout, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile,
                    ssl_context=context, **kwargs
                )
                return
            
            logger.warning("No default email configuration found in database")
            
            # If we're in DEBUG mode and no config was found, use the console backend
            if getattr(settings, 'DEBUG', False) and hasattr(settings, 'FALLBACK_EMAIL_BACKEND'):
                logger.info("Falling back to console email backend")
                self.connection = ConsoleEmailBackend().open()
                return
                
        except Exception as e:
            logger.error(f"Error initializing ConfigurableEmailBackend: {str(e)}")
            
            if getattr(settings, 'DEBUG', False) and hasattr(settings, 'FALLBACK_EMAIL_BACKEND'):
                logger.info(f"Error occurred, falling back to console email backend: {str(e)}")
                self.connection = ConsoleEmailBackend().open()
                return
        
        # If we couldn't get settings from the database and we don't want to use the console backend,
        # fall back to the settings in settings.py
        logger.info("Using email settings from settings.py")
        super().__init__(
            host=host, port=port, username=username, password=password,
            use_tls=use_tls, fail_silently=fail_silently, use_ssl=use_ssl,
            timeout=timeout, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile,
            **kwargs
        )
    
    def open(self):
        """
        Ensure we use our custom SSL context when opening the connection.
        """
        if self.connection:
            return False
        
        try:
            # Create a custom SSL context that disables certificate verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            
            # Set the SSL context
            self.ssl_context = context
            
            # Call the parent method to open the connection
            return super().open()
        except Exception as e:
            if not self.fail_silently:
                raise
            return False 