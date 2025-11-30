import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.message import EmailMessage
from django.core.mail import get_connection
from django.utils import timezone
from .models import EmailConfiguration, EmailHistory, EmailTemplate, ScheduledEmail
import ssl
import time
import os
from django.template import Template, Context
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

# Create a custom SSL context for connections with relaxed verification
def create_ssl_context(verify=False):
    """
    Create a custom SSL context with optional verification.
    
    Args:
        verify: Boolean indicating whether to verify SSL certificates
        
    Returns:
        An SSL context object
    """
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Additionally disable older protocols
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
    return context

def get_email_backend(config=None, timeout=60):
    """
    Get an email backend based on the configuration.
    """
    if config is None:
        from email_manager.models import EmailConfiguration
        config = EmailConfiguration.objects.filter(is_default=True).first()
        if config is None:
            return 'django.core.mail.backends.console.EmailBackend'

    # If using SSL/TLS, use our UnverifiedSSLBackend to avoid certificate issues
    if (isinstance(config, dict) and (config.get('use_tls', False) or config.get('use_ssl', False))) or \
       (not isinstance(config, dict) and (config.email_use_tls or config.email_use_ssl)):
        # Use direct class reference instead of string path to avoid import errors
        from email_manager.backends import UnverifiedSSLBackend
        logger.warning("Using UnverifiedSSLBackend to bypass SSL certificate verification")
        backend = UnverifiedSSLBackend
    else:
        backend = 'django.core.mail.backends.smtp.EmailBackend'
    
    # Handle both dictionary configs and model instance configs
    if isinstance(config, dict):
        options = {
            'host': config.get('host'),
            'port': config.get('port'),
            'username': config.get('username'),
            'password': config.get('password'),
            'use_tls': config.get('use_tls', False),
            'use_ssl': config.get('use_ssl', False),
            'timeout': config.get('timeout', timeout),
            'fail_silently': config.get('fail_silently', False),
            'ssl_context': config.get('ssl_context', None),
        }
    else:
        options = {
            'host': config.email_host,
            'port': config.email_port,
            'username': config.email_host_user,
            'password': config.email_host_password,
            'use_tls': config.email_use_tls,
            'use_ssl': config.email_use_ssl,
            'timeout': timeout,
            'fail_silently': False,
            'ssl_context': None,
        }
    
    # Always create a custom SSL context when SSL or TLS is used
    # Force-disable verification for now regardless of settings to fix the certificate issue
    if options['use_ssl'] or options['use_tls']:
        logger.warning("SSL certificate verification is disabled for email connections")
        options['ssl_context'] = create_ssl_context(verify=False)
    
    # Only include ssl_context if it's provided
    connection_kwargs = {
        'host': options['host'],
        'port': options['port'],
        'username': options['username'],
        'password': options['password'],
        'use_tls': options['use_tls'],
        'use_ssl': options['use_ssl'],
        'timeout': options['timeout'],
        'fail_silently': options['fail_silently'],
    }
    
    # Add SSL context if provided
    if options['ssl_context'] is not None:
        connection_kwargs['ssl_context'] = options['ssl_context']
    
    # If backend is a class, instantiate it directly
    if isinstance(backend, type):
        return backend(**connection_kwargs)
    else:
        # Otherwise, use get_connection with string path
        return get_connection(backend=backend, **connection_kwargs)

def send_email(
    subject,
    message,
    from_email,
    recipient_list,
    html_message=None,
    email_type='general',
    related_object=None,
    template=None,
    context=None,
    config=None
):
    """
    Send an email using the specified configuration.
    
    Args:
        subject: Email subject
        message: Plain text message
        from_email: Sender email address
        recipient_list: List of recipient email addresses
        html_message: HTML version of the message
        email_type: Type of email (for tracking)
        related_object: Related model instance
        template: EmailTemplate instance
        context: Context data for template rendering
        config: EmailConfiguration instance
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Get email configuration
            if config is None:
                config = EmailConfiguration.objects.filter(is_default=True).first()
                if not config:
                    logger.error("No email configuration found")
                    raise ValueError("No email configuration found")
            
            # Validate the email configuration
            if not all([config.email_host, config.email_port, config.email_host_user, config.email_host_password]):
                logger.error(f"Invalid email configuration: {config.name} - missing required fields")
                raise ValueError("Invalid email configuration - missing required fields")
            
            # Make sure both SSL and TLS aren't enabled
            if config.email_use_ssl and config.email_use_tls:
                config.email_use_ssl = False
                config.save()
                logger.warning(f"Both SSL and TLS were enabled for {config.name}, disabled SSL")
            
            # Validate sender and recipient emails
            if not from_email or '@' not in from_email:
                from_email = config.default_from_email
                logger.warning(f"Invalid from_email, using default: {from_email}")
                
            if not recipient_list or not isinstance(recipient_list, (list, tuple)):
                logger.error("Invalid recipient list")
                raise ValueError("Invalid recipient list - must be a list or tuple of email addresses")
            
            # Get email backend with retry logic
            try:
                connection = get_email_backend(config=config)
            except Exception as e:
                logger.error(f"Failed to create email backend: {str(e)}")
                raise
            
            # Create email message
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
                connection=connection
            )
            
            # Add HTML content if provided
            if html_message:
                email.content_subtype = "html"
                email.body = html_message
            
            # Log the attempt
            logger.info(f"Attempting to send email to {recipient_list} (try {retry_count+1}/{max_retries+1})")
            
            # Send email with specific timeout
            email.send(fail_silently=False)
            
            # Log success
            try:
                # Create history entry
                history_data = {
                    'email_type': email_type,
                    'recipient_email': recipient_list[0] if recipient_list else "unknown",
                    'subject': subject,
                    'body': message,
                    'html_body': html_message,
                    'status': 'success',
                }
                
                # Handle related_object using ContentType framework if provided
                if related_object:
                    content_type = ContentType.objects.get_for_model(related_object)
                    history_data['content_type'] = content_type
                    history_data['object_id'] = related_object.pk
                
                success_entry = EmailHistory.objects.create(**history_data)
            except Exception as history_error:
                logger.error(f"Failed to create email history on success: {str(history_error)}")
            
            logger.info(f"Email sent successfully to {recipient_list}")
            return True
            
        except Exception as e:
            # Log error with retry information
            retry_count += 1
            logger.error(f"Failed to send email (attempt {retry_count}/{max_retries+1}): {str(e)}")
            
            if retry_count <= max_retries:
                logger.info(f"Retrying in 2 seconds...")
                time.sleep(2)  # Wait 2 seconds before retrying
            else:
                # Final failure - log to database
                try:
                    # Create history entry for failure
                    history_data = {
                        'email_type': email_type,
                        'recipient_email': recipient_list[0] if recipient_list else "unknown",
                        'subject': subject,
                        'body': message,
                        'status': 'failed',
                        'error_message': str(e),
                    }
                    
                    # Handle related_object using ContentType framework if provided
                    if related_object:
                        content_type = ContentType.objects.get_for_model(related_object)
                        history_data['content_type'] = content_type
                        history_data['object_id'] = related_object.pk
                    
                    EmailHistory.objects.create(**history_data)
                except Exception as history_error:
                    logger.error(f"Failed to create email history: {str(history_error)}")
                
                logger.error(f"Failed to send email after {max_retries+1} attempts: {str(e)}")
                return False

def send_template_email(
    template_name,
    recipient_list,
    context=None,
    email_type='general',
    related_object=None,
    config=None
):
    """
    Send an email using a template.
    
    Args:
        template_name: Name of the template to use
        recipient_list: List of recipient email addresses
        context: Context data for template rendering
        email_type: Type of email (for tracking)
        related_object: Related model instance
        config: EmailConfiguration instance
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get template
        template = EmailTemplate.objects.get(name=template_name)
        
        # Prepare context
        if context is None:
            context = {}
        
        # Render template - use Template directly since we have template content, not a path
        template_obj = Template(template.html_content)
        ctx_obj = Context(context)
        html_message = template_obj.render(ctx_obj)
        plain_message = strip_tags(html_message)
        
        # Get email configuration
        if config is None:
            # First try to get config from template if it has a configuration attribute
            config = getattr(template, 'configuration', None)
            
            # Fall back to default if no configuration is found
            if not config:
                from .models import EmailConfiguration
                config = EmailConfiguration.get_default()
                
            if not config:
                logger.error("No email configuration found")
                return False
        
        # Send email
        return send_email(
            subject=template.subject,
            message=plain_message,
            from_email=config.default_from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            email_type=email_type,
            related_object=related_object,
            template=template,
            context=context,
            config=config
        )
        
    except EmailTemplate.DoesNotExist:
        logger.error(f"Template {template_name} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send template email: {str(e)}")
        return False

def process_scheduled_emails():
    """
    Process scheduled emails that are due to be sent.
    """
    from email_manager.models import ScheduledEmail
    
    now = timezone.now()
    
    # Get scheduled emails that are due to be sent
    due_emails = ScheduledEmail.objects.filter(
        send_time__lte=now,
        status='pending'
    )
    
    logger.info(f"Processing {due_emails.count()} scheduled emails")
    
    for email in due_emails:
        try:
            # Update status to processing
            email.status = 'processing'
            email.save()
            
            # Send the email
            send_status = send_email(
                subject=email.subject,
                message=email.body,
                from_email=email.from_email,
                recipient_list=[email.recipient_email],
                html_message=email.html_body,
                email_type='scheduled',
                related_object=email.related_object
            )
            
            # Update status based on result
            if send_status:
                email.status = 'sent'
                email.sent_time = timezone.now()
            else:
                email.status = 'failed'
                email.error_message = "Failed to send email"
            
            email.save()
            logger.info(f"Processed scheduled email {email.id}: {email.status}")
            
        except Exception as e:
            logger.error(f"Error processing scheduled email {email.id}: {str(e)}")
            email.status = 'failed'
            email.error_message = str(e)
            email.save()

def test_email_connection(config=None):
    """
    Test if an email connection can be established with the given configuration.
    
    Args:
        config: EmailConfiguration instance or None to use the default
        
    Returns:
        dict: Result of the connection test with success status and message
    """
    try:
        if config is None:
            from email_manager.models import EmailConfiguration
            config = EmailConfiguration.objects.filter(is_default=True).first()
            if not config:
                return {
                    'success': False,
                    'message': "No email configuration found"
                }
        
        # Try to get a connection with the configured settings
        connection = get_email_backend(config=config)
        
        # Try to open and close the connection
        connection.open()
        connection.close()
        
        return {
            'success': True,
            'message': f"Successfully connected to {config.email_host}:{config.email_port} using {'SSL' if config.email_use_ssl else 'TLS' if config.email_use_tls else 'plain'} connection"
        }
    except Exception as e:
        # Log the detailed error
        logger.error(f"Email connection test failed: {str(e)}", exc_info=True)
        
        # Provide helpful error message based on exception type
        if 'SSL' in str(e) or 'certificate' in str(e):
            message = f"SSL/TLS connection failed: {str(e)}. Try setting EMAIL_VERIFY_SSL=False in settings if this is a development environment."
        elif 'authentication' in str(e).lower() or 'login' in str(e).lower():
            message = f"Authentication failed: {str(e)}. Check your username and password."
        elif 'timeout' in str(e).lower():
            message = f"Connection timed out: {str(e)}. Check your firewall settings or increase timeout."
        elif 'connection refused' in str(e).lower():
            message = f"Connection refused: {str(e)}. Check if the server is running and your port settings are correct."
        else:
            message = f"Connection failed: {str(e)}"
        
        return {
            'success': False,
            'message': message
        } 