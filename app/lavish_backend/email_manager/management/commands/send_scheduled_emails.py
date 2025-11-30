from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template import Template, Context, Engine
from django.core.mail import EmailMultiAlternatives, send_mail, get_connection
from kora.models import ScheduledEmail, EmailConfiguration
from kora.utils import save_emails_to_files
import logging
import smtplib
import socket
import ssl
import os

# Set a global socket timeout to prevent server hanging
socket.setdefaulttimeout(15)  # 15 seconds timeout

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process pending scheduled emails and send them using configured email settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sending of emails even if they are not yet due',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of emails to process',
            default=None
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed information during processing',
        )
        parser.add_argument(
            '--email-id',
            type=int,
            help='Process a specific email by ID',
            default=None
        )

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']
        verbose = options['verbose']
        email_id = options['email_id']
        
        self.stdout.write(self.style.SUCCESS('Starting scheduled email processing'))
        
        # Get the current time
        now = timezone.now()
        
        # Find scheduled emails that are pending and due to be sent
        if email_id:
            query = ScheduledEmail.objects.filter(id=email_id)
            if verbose:
                self.stdout.write(f"Processing specific email ID: {email_id}")
        else:
            query = ScheduledEmail.objects.filter(status='pending')
            
            if not force:
                query = query.filter(scheduled_time__lte=now)
            
            if limit:
                query = query[:limit]
        
        pending_emails = query
        
        if verbose:
            self.stdout.write(f"Found {pending_emails.count()} pending emails to send")
        
        # Get default email configuration if needed
        default_config = EmailConfiguration.objects.filter(is_default=True).first()
        
        if not default_config and verbose:
            self.stdout.write(self.style.WARNING('No default email configuration found'))
        
        success_count = 0
        failure_count = 0
        
        # Create template engine with built-in libraries
        engine = Engine.get_default()
        
        # List to collect failed emails for fallback saving
        failed_emails = []
        
        for email in pending_emails:
            try:
                if verbose:
                    self.stdout.write(f"Processing email: {email.subject_override or email.template.subject}")
                
                # Get email configuration - use configuration priority:
                # 1. ScheduledEmail's configuration if set
                # 2. Template's configuration if set
                # 3. Default configuration
                config = None
                if email.configuration:
                    config = email.configuration
                    if verbose:
                        self.stdout.write(f"Using email-specific configuration: {config.name}")
                elif email.template.configuration:
                    config = email.template.configuration
                    if verbose:
                        self.stdout.write(f"Using template configuration: {config.name}")
                else:
                    config = default_config
                    if verbose and default_config:
                        self.stdout.write(f"Using default configuration: {default_config.name}")
                
                if not config:
                    raise Exception("No email configuration found for sending")
                
                # Get template content and subject
                subject = email.subject_override or email.template.subject
                html_content = email.template.html_content
                plain_text_content = email.template.plain_text_content
                
                # Prepend load statements for common template tags
                html_content = "{% load static i18n %}\n" + html_content
                plain_text_content = "{% load static i18n %}\n" + plain_text_content
                
                # Replace variables in the content
                if email.variables_data:
                    ctx = Context(email.variables_data)
                    
                    # Use the engine with Django built-in template tags
                    template_html = engine.from_string(html_content)
                    template_plain = engine.from_string(plain_text_content)
                    template_subject = engine.from_string(subject)
                    
                    html_content = template_html.render(ctx)
                    plain_text_content = template_plain.render(ctx)
                    subject = template_subject.render(ctx)
                
                # Prepare email parameters
                from_email = config.default_from_email
                recipients = email.recipients
                
                if verbose:
                    self.stdout.write(f"Sending email to {len(recipients)} recipients")
                
                # Try different SMTP configurations
                sent = False
                last_error = None
                
                # Try in order of most likely to succeed based on test results
                
                # Attempt 1: Try using TLS on port 587 with verification disabled
                try:
                    if verbose:
                        self.stdout.write("Trying port 587 with TLS and SSL verification disabled...")
                    
                    # Create a custom SSL context with verification disabled
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    connection = get_connection(
                        backend='django.core.mail.backends.smtp.EmailBackend',
                        host=config.email_host,
                        port=587,
                        username=config.email_host_user,
                        password=config.email_host_password,
                        use_tls=True,
                        use_ssl=False,
                        timeout=15,
                        ssl_context=context  # Use our disabled verification context
                    )
                    
                    # Create email message
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=plain_text_content,
                        from_email=from_email,
                        to=recipients,
                        connection=connection
                    )
                    
                    # Attach HTML content
                    if html_content:
                        msg.attach_alternative(html_content, "text/html")
                    
                    msg.send()
                    sent = True
                    
                    if verbose:
                        self.stdout.write(self.style.SUCCESS("Email sent using TLS on port 587 with SSL verification disabled"))
                    
                except Exception as e:
                    last_error = e
                    if verbose:
                        self.stdout.write(self.style.WARNING(f"TLS port 587 method with disabled verification failed: {str(e)}"))
                
                # Attempt 2: Try using SSL on port 465 with verification disabled
                if not sent:
                    try:
                        if verbose:
                            self.stdout.write("Trying port 465 with SSL and SSL verification disabled...")
                        
                        # Create a custom SSL context with verification disabled
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        connection = get_connection(
                            backend='django.core.mail.backends.smtp.EmailBackend',
                            host=config.email_host,
                            port=465,
                            username=config.email_host_user,
                            password=config.email_host_password,
                            use_tls=False,
                            use_ssl=True,
                            timeout=15,
                            ssl_context=context  # Use our disabled verification context
                        )
                        
                        # Create email message
                        msg = EmailMultiAlternatives(
                            subject=subject,
                            body=plain_text_content,
                            from_email=from_email,
                            to=recipients,
                            connection=connection
                        )
                        
                        # Attach HTML content
                        if html_content:
                            msg.attach_alternative(html_content, "text/html")
                        
                        msg.send()
                        sent = True
                        
                        if verbose:
                            self.stdout.write(self.style.SUCCESS("Email sent using SSL on port 465 with SSL verification disabled"))
                        
                    except Exception as e:
                        last_error = e
                        if verbose:
                            self.stdout.write(self.style.WARNING(f"SSL port 465 method with disabled verification failed: {str(e)}"))
                
                # Attempt 3: Now try using the configured settings if above methods failed
                if not sent:
                    try:
                        if verbose:
                            self.stdout.write("Trying with configured settings...")
                        
                        connection = self.get_connection(config)
                        
                        # Create email message
                        msg = EmailMultiAlternatives(
                            subject=subject,
                            body=plain_text_content,
                            from_email=from_email,
                            to=recipients,
                            connection=connection
                        )
                        
                        # Attach HTML content
                        if html_content:
                            msg.attach_alternative(html_content, "text/html")
                        
                        msg.send()
                        sent = True
                        
                        if verbose:
                            self.stdout.write(self.style.SUCCESS("Email sent using primary configuration"))
                        
                    except Exception as e:
                        last_error = e
                        if verbose:
                            self.stdout.write(self.style.WARNING(f"Primary sending method failed: {str(e)}"))
                
                # Attempt 4: Try using direct SMTP connection as last resort
                if not sent:
                    try:
                        if verbose:
                            self.stdout.write("Trying direct SMTP connection...")
                        
                        # Try to connect directly to the SMTP server
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        # Connect to the SMTP server
                        if config.email_use_ssl:
                            server = smtplib.SMTP_SSL(config.email_host, config.email_port, context=context)
                        else:
                            server = smtplib.SMTP(config.email_host, config.email_port)
                            
                            if config.email_use_tls:
                                server.starttls(context=context)
                        
                        # Some servers don't require authentication
                        try:
                            if config.email_host_user and config.email_host_password:
                                server.login(config.email_host_user, config.email_host_password)
                            else:
                                if verbose:
                                    self.stdout.write(self.style.WARNING("No authentication credentials provided"))
                        except smtplib.SMTPException as e:
                            if verbose:
                                self.stdout.write(self.style.WARNING(f"SMTP authentication failed, continuing without auth: {str(e)}"))
                        
                        # Create message
                        from email.mime.multipart import MIMEMultipart
                        from email.mime.text import MIMEText
                        
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = from_email
                        msg['To'] = ', '.join(recipients)
                        
                        part1 = MIMEText(plain_text_content, 'plain')
                        part2 = MIMEText(html_content, 'html')
                        
                        msg.attach(part1)
                        msg.attach(part2)
                        
                        # Send the email
                        server.send_message(msg)
                        server.quit()
                        sent = True
                        
                        if verbose:
                            self.stdout.write(self.style.SUCCESS("Email sent using direct SMTP connection"))
                        
                    except Exception as e:
                        last_error = e
                        if verbose:
                            self.stdout.write(self.style.WARNING(f"Direct SMTP connection failed: {str(e)}"))
                
                # If email was sent successfully, update the record
                if sent:
                    email.status = 'sent'
                    email.sent_time = timezone.now()
                    email.save()
                    
                    success_count += 1
                    
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"Email sent successfully to {', '.join(recipients)}"))
                else:
                    # If all attempts failed and email could not be sent
                    # Add to list of failed emails for fallback saving to files
                    failed_emails.append({
                        'subject': subject,
                        'message': plain_text_content,
                        'html_message': html_content,
                        'recipients': recipients,
                        'from_email': from_email,
                        'email_id': email.id
                    })
                    
                    # Update error status in database
                    error_msg = f"All sending methods failed. Last error: {str(last_error)}"
                    logger.error(error_msg)
                    
                    if verbose:
                        self.stdout.write(self.style.ERROR(error_msg))
                    
                    email.attempts += 1
                    email.last_attempt = timezone.now()
                    email.error_message = error_msg
                    
                    # Check if max attempts reached
                    if email.attempts >= 3:  # Maximum 3 attempts
                        email.status = 'failed'
                    
                    email.save()
                    failure_count += 1
                
            except Exception as e:
                # Log the error and update the email status
                error_msg = f"Error processing email: {str(e)}"
                logger.error(error_msg)
                
                # Try to add to failed emails list if we have enough info
                try:
                    subject = email.subject_override or email.template.subject
                    failed_emails.append({
                        'subject': subject,
                        'message': plain_text_content if 'plain_text_content' in locals() else "Error processing email",
                        'html_message': html_content if 'html_content' in locals() else None,
                        'recipients': email.recipients,
                        'from_email': from_email if 'from_email' in locals() else "system@example.com",
                        'email_id': email.id
                    })
                except Exception as inner_e:
                    logger.error(f"Could not add failed email to fallback list: {str(inner_e)}")
                
                if verbose:
                    self.stdout.write(self.style.ERROR(error_msg))
                
                email.attempts += 1
                email.last_attempt = timezone.now()
                email.error_message = str(e)
                
                # Check if max attempts reached
                if email.attempts >= 3:  # Maximum 3 attempts
                    email.status = 'failed'
                
                email.save()
                failure_count += 1
        
        # If we have failed emails, try to save them as files
        if failed_emails:
            saved_count = save_emails_to_files(failed_emails)
            if verbose and saved_count > 0:
                self.stdout.write(self.style.WARNING(f"Saved {saved_count} failed emails to files for review"))
        
        total = success_count + failure_count
        if total > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed {total} emails: {success_count} sent successfully, {failure_count} failed"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("No pending emails to process"))

    def get_connection(self, config, port=None, use_tls=None, use_ssl=None):
        """Get a connection to the email server with configurable settings"""
        from django.core.mail import get_connection
        
        # Use provided values or fall back to configuration
        port = port if port is not None else config.email_port
        use_tls = use_tls if use_tls is not None else config.email_use_tls
        use_ssl = use_ssl if use_ssl is not None else config.email_use_ssl
        
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=config.email_host,
            port=port,
            username=config.email_host_user,
            password=config.email_host_password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            # Use a shorter timeout to prevent server blocking
            timeout=15,
            # Connect and authenticate proactively to detect issues early
            fail_silently=False
        ) 