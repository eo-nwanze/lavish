"""
Email sending utilities for ENDEVOPS
Integrates email_manager with existing forms
"""
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from .models import EmailConfiguration, EmailTemplate, EmailHistory
import logging

logger = logging.getLogger(__name__)


def send_template_email(template_name, recipient_email, context_data, config_email=None):
    """
    Send an email using a template
    
    Args:
        template_name: Name of the EmailTemplate to use
        recipient_email: Recipient's email address
        context_data: Dictionary of template variables
        config_email: Email config to use (info@endevops.com or support@endevops.com)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        # Get the appropriate email configuration
        if config_email:
            email_config = EmailConfiguration.objects.get(email_host_user=config_email)
        else:
            email_config = EmailConfiguration.get_default()
        
        if not email_config:
            logger.error("No email configuration found")
            return {'success': False, 'message': 'Email configuration not found'}
        
        # Get the template
        try:
            if isinstance(template_name, str):
                email_template = EmailTemplate.objects.get(name=template_name, is_active=True)
            else:
                # Assume it's a template_type
                email_template = EmailTemplate.objects.get(template_type=template_name, is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template '{template_name}' not found")
            return {'success': False, 'message': f'Template {template_name} not found'}
        
        # Render the subject and body with context
        subject_template = Template(email_template.subject)
        html_template = Template(email_template.html_content)
        plain_template = Template(email_template.plain_text_content)
        
        context = Context(context_data)
        subject = subject_template.render(context)
        html_body = html_template.render(context)
        plain_body = plain_template.render(context)
        
        # Create the email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=email_config.default_from_email,
            to=[recipient_email],
            connection=get_email_connection(email_config)
        )
        email.attach_alternative(html_body, "text/html")
        
        # Send the email
        email.send()
        
        # Log the email in history
        EmailHistory.objects.create(
            email_type=email_template.template_type,
            recipient_email=recipient_email,
            subject=subject,
            body=plain_body,
            html_body=html_body,
            status='success'
        )
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return {'success': True, 'message': 'Email sent successfully'}
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        
        # Log the failed email
        try:
            EmailHistory.objects.create(
                email_type='other',
                recipient_email=recipient_email,
                subject=context_data.get('subject', 'Email sending failed'),
                body=str(context_data),
                status='failed',
                error_message=str(e)
            )
        except:
            pass
        
        return {'success': False, 'message': str(e)}


def get_email_connection(email_config):
    """
    Create a Django email backend connection from EmailConfiguration
    """
    from django.core.mail import get_connection
    
    return get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=email_config.email_host,
        port=email_config.email_port,
        username=email_config.email_host_user,
        password=email_config.email_host_password,
        use_tls=email_config.email_use_tls,
        use_ssl=email_config.email_use_ssl,
        fail_silently=False,
    )


def send_contact_form_email(name, email, phone, subject, message, submission_date):
    """
    Send contact form notification to info@endevops.com
    """
    context = {
        'name': name,
        'email': email,
        'phone': phone or 'Not provided',
        'subject': subject or 'General Inquiry',
        'message': message,
        'submission_date': submission_date,
    }
    
    return send_template_email(
        template_name='Contact Form Notification',
        recipient_email='info@endevops.com',
        context_data=context,
        config_email='info@endevops.com'
    )


def send_appointment_confirmation(client_name, client_email, service_name, appointment_date, appointment_time, confirmation_code, duration=None, meeting_type=None, notes=None):
    """
    Send appointment confirmation to client
    """
    context = {
        'client_name': client_name,
        'service_name': service_name,
        'appointment_date': appointment_date,
        'appointment_time': appointment_time,
        'confirmation_code': confirmation_code,
        'duration': duration or '60 minutes',
        'meeting_type': meeting_type or 'Video Conference',
        'notes': notes,
        'reschedule_link': 'https://www.endevops.com/appointments/',
        'cancel_link': 'https://www.endevops.com/appointments/',
    }
    
    return send_template_email(
        template_name='Appointment Confirmation',
        recipient_email=client_email,
        context_data=context,
        config_email='info@endevops.com'
    )


def send_ticket_confirmation(customer_name, customer_email, ticket_number, category, priority, subject, message, submission_date, status='OPEN'):
    """
    Send ticket submission confirmation to customer
    """
    context = {
        'customer_name': customer_name,
        'customer_email': customer_email,
        'ticket_number': ticket_number,
        'category': category,
        'priority': priority.upper(),
        'subject': subject,
        'message': message,
        'submission_date': submission_date,
        'status': status,
        'ticket_link': f'https://www.endevops.com/tickets/{ticket_number}/',
    }
    
    return send_template_email(
        template_name='Ticket Submission Confirmation',
        recipient_email=customer_email,
        context_data=context,
        config_email='support@endevops.com'
    )
