import ssl
import logging
import os
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)

# Globally disable SSL certificate verification at the Python environment level
os.environ['PYTHONHTTPSVERIFY'] = '0'

class UnverifiedSSLBackend(EmailBackend):
    """
    SMTP backend that completely bypasses SSL certificate verification.
    
    This is useful for development environments where self-signed 
    certificates might be used, or when connecting to mail servers 
    with expired or otherwise invalid certificates.
    
    WARNING: This should not be used in production unless absolutely necessary,
    as it bypasses security measures that protect against MITM attacks.
    """
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        
        # Create and configure a completely insecure SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Disable legacy SSL/TLS protocols for better security
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        # Set a non-default HTTPS certificate path that will cause Python to ignore verification
        # This is an alternative approach for Python 3.13 which requires more aggressive disabling
        if hasattr(ssl, '_https_verify_certificates'):
            ssl._https_verify_certificates(enable=False)
        
        # Force the use of our custom SSL context
        kwargs['ssl_context'] = context
        
        logger.warning("Using UnverifiedSSLBackend - ALL SSL certificate verification is disabled!")
        
        super().__init__(
            host=host, port=port, username=username, password=password,
            use_tls=use_tls, fail_silently=fail_silently, use_ssl=use_ssl,
            timeout=timeout, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile,
            **kwargs
        )
    
    def open(self):
        """
        Completely custom implementation of the open method that uses smtplib directly.
        
        This ensures our SSL context is used properly.
        """
        if self.connection:
            return False

        # Use smtplib directly
        import smtplib
        
        try:
            # Create a new SSL context to ensure verification is disabled
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.ssl_context = ssl_context
            
            logger.info(f"Connecting to SMTP server: {self.host}:{self.port}")
            
            if self.use_ssl:
                self.connection = smtplib.SMTP_SSL(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout,
                    context=ssl_context
                )
                logger.info("Using SMTP_SSL connection with SSL verification disabled")
            else:
                self.connection = smtplib.SMTP(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout
                )
                if self.use_tls:
                    # Explicitly pass our SSL context to starttls
                    self.connection.starttls(context=ssl_context)
                    logger.info("Using SMTP with STARTTLS with SSL verification disabled")
                else:
                    logger.info("Using plain SMTP connection")
            
            if self.username and self.password:
                logger.info(f"Logging in as {self.username}")
                self.connection.login(self.username, self.password)
                
            return True
        except Exception as e:
            if not self.fail_silently:
                logger.error(f"Error establishing SMTP connection: {str(e)}", exc_info=True)
                raise
            return False 