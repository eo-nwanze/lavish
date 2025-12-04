from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from .models import (
    EmailConfiguration,
    EmailTemplate,
    EmailHistory,
    ScheduledEmail,
    Newsletter,
    NewsletterSubscriber,
    EmailInbox,
    EmailMessage,
    EmailAttachment,
    EmailGuardian,
    SecurityAlert,
    EmailAutomation,
    EmailFolder,
    EmailLabel,
    MessageLabel
)
from .forms import (
    EmailConfigurationForm,
    EmailTemplateForm,
    NewsletterForm,
    NewsletterSubscriberForm,
    EmailInboxForm,
    EmailMessageForm,
    EmailGuardianForm,
    EmailAutomationForm,
    EmailFolderForm,
    EmailLabelForm,
    EmailAttachmentForm
)
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import logging
import ssl
from datetime import datetime
import json
import socket
import uuid
from django.core.mail import get_connection
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.template import Template, Context
from email_manager.utils import get_email_backend
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Create your views here.

@login_required
def inbox_list(request):
    """Display the user's email inbox with support for multiple accounts."""
    # Get all active inboxes
    all_inboxes = EmailInbox.objects.filter(is_active=True)
    
    # Get selected inbox from query param or default to first inbox
    inbox_id = request.GET.get('inbox')
    if inbox_id:
        inbox = get_object_or_404(EmailInbox, pk=inbox_id, is_active=True)
    else:
        inbox = all_inboxes.first()
    
    if not inbox:
        messages.info(request, 'No active email inbox found. Please contact the administrator.')
        return render(request, 'email_manager/no_inbox.html')
    
    folder_id = request.GET.get('folder')
    search_query = request.GET.get('q')
    view_all = request.GET.get('view_all') == 'true'
    
    # Get messages from selected inbox or all inboxes
    if view_all:
        email_messages = EmailMessage.objects.filter(inbox__is_active=True)
    else:
        email_messages = EmailMessage.objects.filter(inbox=inbox)
    
    if folder_id:
        email_messages = email_messages.filter(folder_id=folder_id)
    
    if search_query:
        email_messages = email_messages.filter(
            Q(subject__icontains=search_query) |
            Q(body__icontains=search_query) |
            Q(from_email__icontains=search_query)
        )
    
    # Order by received date
    email_messages = email_messages.order_by('-received_at', '-created_at')
    
    paginator = Paginator(email_messages, 20)
    page = request.GET.get('page')
    email_messages = paginator.get_page(page)
    
    context = {
        'inbox': inbox,
        'all_inboxes': all_inboxes,
        'messages': email_messages,
        'folders': EmailFolder.objects.all(),
        'labels': EmailLabel.objects.all(),
        'view_all': view_all,
    }
    return render(request, 'email_manager/inbox_list.html', context)

@login_required
def message_detail(request, pk):
    """Display email message details."""
    message = get_object_or_404(EmailMessage, pk=pk, inbox__email_address=request.user.email)
    message.is_read = True
    message.save()
    
    context = {
        'message': message,
        'attachments': message.attachments.all(),
        'labels': message.labels.all(),
    }
    return render(request, 'email_manager/message_detail.html', context)

@login_required
def compose_message(request):
    """Compose a new email message."""
    if request.method == 'POST':
        form = EmailMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.inbox = get_object_or_404(EmailInbox, email_address=request.user.email)
            message.from_email = request.user.email
            message.created_by = request.user
            message.save()
            
            # Handle attachments
            for file in request.FILES.getlist('attachments'):
                EmailAttachment.objects.create(
                    message=message,
                    file=file,
                    filename=file.name,
                    content_type=file.content_type,
                    size=file.size
                )
            
            messages.success(request, 'Message saved successfully.')
            return redirect('email_manager:message_detail', pk=message.pk)
    else:
        form = EmailMessageForm()
    
    return render(request, 'email_manager/compose_message.html', {'form': form})

@login_required
def reply_message(request, pk):
    """Reply to an email message."""
    original_message = get_object_or_404(EmailMessage, pk=pk, inbox__email_address=request.user.email)
    
    if request.method == 'POST':
        form = EmailMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.inbox = get_object_or_404(EmailInbox, email_address=request.user.email)
            message.from_email = request.user.email
            message.created_by = request.user
            message.parent_message = original_message
            message.save()
            
            original_message.is_replied = True
            original_message.save()
            
            messages.success(request, 'Reply sent successfully.')
            return redirect('email_manager:message_detail', pk=message.pk)
    else:
        form = EmailMessageForm(initial={
            'subject': f"Re: {original_message.subject}",
            'to_emails': [original_message.from_email],
            'cc_emails': original_message.to_emails,
        })
    
    return render(request, 'email_manager/reply_message.html', {
        'form': form,
        'original_message': original_message
    })

@login_required
def forward_message(request, pk):
    """Forward an email message."""
    original_message = get_object_or_404(EmailMessage, pk=pk, inbox__email_address=request.user.email)
    
    if request.method == 'POST':
        form = EmailMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.inbox = get_object_or_404(EmailInbox, email_address=request.user.email)
            message.from_email = request.user.email
            message.created_by = request.user
            message.parent_message = original_message
            message.save()
            
            original_message.is_forwarded = True
            original_message.save()
            
            messages.success(request, 'Message forwarded successfully.')
            return redirect('email_manager:message_detail', pk=message.pk)
    else:
        form = EmailMessageForm(initial={
            'subject': f"Fwd: {original_message.subject}",
            'body': f"\n\n---------- Forwarded message ----------\nFrom: {original_message.from_email}\nDate: {original_message.created_at}\nSubject: {original_message.subject}\n\n{original_message.body}"
        })
    
    return render(request, 'email_manager/forward_message.html', {
        'form': form,
        'original_message': original_message
    })

@login_required
def toggle_favorite(request, pk):
    """Toggle favorite status of a message."""
    message = get_object_or_404(EmailMessage, pk=pk, inbox__email_address=request.user.email)
    message.is_favorite = not message.is_favorite
    message.save()
    return JsonResponse({'is_favorite': message.is_favorite})

@login_required
def add_label(request, pk):
    """Add a label to a message."""
    message = get_object_or_404(EmailMessage, pk=pk, inbox__email_address=request.user.email)
    label = get_object_or_404(EmailLabel, pk=request.POST.get('label_id'))
    
    MessageLabel.objects.get_or_create(message=message, label=label)
    return JsonResponse({'success': True})

@login_required
def remove_label(request, pk):
    """Remove a label from a message."""
    message = get_object_or_404(EmailMessage, pk=pk, inbox__email_address=request.user.email)
    label = get_object_or_404(EmailLabel, pk=request.POST.get('label_id'))
    
    MessageLabel.objects.filter(message=message, label=label).delete()
    return JsonResponse({'success': True})

@login_required
def guardian_list(request):
    """List email guardian rules."""
    guardians = EmailGuardian.objects.all()
    return render(request, 'email_manager/guardian_list.html', {'guardians': guardians})

@login_required
def guardian_create(request):
    """Create a new email guardian rule."""
    if request.method == 'POST':
        form = EmailGuardianForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guardian rule created successfully.')
            return redirect('email_manager:guardian_list')
    else:
        form = EmailGuardianForm()
    
    return render(request, 'email_manager/guardian_form.html', {'form': form})

@login_required
def guardian_edit(request, pk):
    """Edit an email guardian rule."""
    guardian = get_object_or_404(EmailGuardian, pk=pk)
    
    if request.method == 'POST':
        form = EmailGuardianForm(request.POST, instance=guardian)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guardian rule updated successfully.')
            return redirect('email_manager:guardian_list')
    else:
        form = EmailGuardianForm(instance=guardian)
    
    return render(request, 'email_manager/guardian_form.html', {'form': form})

@login_required
def automation_list(request):
    """List email automation rules."""
    automations = EmailAutomation.objects.all()
    return render(request, 'email_manager/automation_list.html', {'automations': automations})

@login_required
def automation_create(request):
    """Create a new email automation rule."""
    if request.method == 'POST':
        form = EmailAutomationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Automation rule created successfully.')
            return redirect('email_manager:automation_list')
    else:
        form = EmailAutomationForm()
    
    return render(request, 'email_manager/automation_form.html', {'form': form})

@login_required
def automation_edit(request, pk):
    """Edit an email automation rule."""
    automation = get_object_or_404(EmailAutomation, pk=pk)
    
    if request.method == 'POST':
        form = EmailAutomationForm(request.POST, instance=automation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Automation rule updated successfully.')
            return redirect('email_manager:automation_list')
    else:
        form = EmailAutomationForm(instance=automation)
    
    return render(request, 'email_manager/automation_form.html', {'form': form})

@login_required
def security_alerts(request):
    """Display security alerts."""
    alerts = SecurityAlert.objects.filter(is_resolved=False).order_by('-created_at')
    return render(request, 'email_manager/security_alerts.html', {'alerts': alerts})

@login_required
def resolve_alert(request, pk):
    """Mark a security alert as resolved."""
    alert = get_object_or_404(SecurityAlert, pk=pk)
    alert.is_resolved = True
    alert.resolved_at = timezone.now()
    alert.save()
    return JsonResponse({'success': True})

@csrf_exempt
def test_email_config(request, config_id):
    """
    Tests an email configuration by sending a test email
    """
    # Add CORS headers for all responses
    def create_json_response(data, status=200):
        response = JsonResponse(data, status=status)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type, X-CSRFToken"
        return response
    
    # Log request details to debug URL routing issues
    logger.info(f"Received request to test_email_config: {request.method} for config_id={config_id}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Handle OPTIONS request (preflight)
    if request.method == 'OPTIONS':
        return create_json_response({'status': 'ok'})
    
    if request.method != 'POST':
        return create_json_response({'status': 'error', 'message': 'Only POST requests are allowed'}, 405)
    
    try:
        # Parse JSON request data
        try:
            request_body = request.body.decode('utf-8')
            logger.debug(f"Request body: {request_body}")
            data = json.loads(request_body)
            to_email = data.get('email')
            template_id = data.get('template_id')
            set_as_default = data.get('set_as_default', False)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            logger.error(f"Raw request body: {request.body}")
            return create_json_response({
                'status': 'error', 
                'message': f'Invalid JSON data: {str(e)}'
            }, 400)
        
        # Validate email
        if not to_email:
            return create_json_response({
                'status': 'error', 
                'message': 'Email address is required'
            }, 400)
        
        # Get the email configuration
        try:
            config = EmailConfiguration.objects.get(pk=config_id)
            logger.info(f"Found email configuration: {config.name} (ID: {config_id})")
        except EmailConfiguration.DoesNotExist:
            logger.error(f"Email configuration with ID {config_id} not found")
            return create_json_response({
                'status': 'error', 
                'message': f'Email configuration with ID {config_id} not found'
            }, 404)
        
        # Look for template if ID provided
        template = None
        if template_id:
            try:
                template = EmailTemplate.objects.get(pk=template_id)
                logger.info(f"Using template {template.name} (ID: {template_id}) for test email")
                
                # If set as default, update the configuration
                if set_as_default and template:
                    config.default_template_id = template.id
                    config.save()
                    logger.info(f"Set template {template.name} (ID: {template_id}) as default for config {config.name}")
            except EmailTemplate.DoesNotExist:
                logger.warning(f"Template with ID {template_id} not found, will use default template or plain text email")
        
        # If no template specified, try to get the default template for this config
        if not template and config.default_template_id:
            try:
                template = EmailTemplate.objects.get(pk=config.default_template_id)
                logger.info(f"Using default template {template.name} for config {config.name}")
            except EmailTemplate.DoesNotExist:
                logger.warning(f"Default template ID {config.default_template_id} not found")
        
        # Create a custom SSL context for development
        context_ssl = ssl.create_default_context()
        context_ssl.check_hostname = False
        context_ssl.verify_mode = ssl.CERT_NONE
        # Disable all certificate validation completely
        context_ssl.options |= ssl.OP_NO_SSLv2
        context_ssl.options |= ssl.OP_NO_SSLv3
        
        # Log the connection details for debugging
        logger.info(f"Connecting to {config.email_host}:{config.email_port} with user {config.email_host_user}")
        logger.info(f"TLS: {config.email_use_tls}, SSL: {config.email_use_ssl}")
        
        # Prepare context variables for template
        context = {
            'configuration_name': config.name,
            'config_name': config.name,
            'server_name': socket.gethostname(),
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'email_address': to_email,
            'recipient_email': to_email,
            'recipient_name': to_email.split('@')[0] if '@' in to_email else 'User',
            'sender': config.default_from_email,
            'sender_email': config.default_from_email,
            'sender_name': config.name,
            'current_year': timezone.now().year,
            'current_date': timezone.now().strftime('%Y-%m-%d'),
            'username': to_email.split('@')[0] if '@' in to_email else 'User',
        }
        
        # Subject for the email
        subject = f"Test Email from {config.name}"
        
        # If a template is found, use it
        if template:
            # Get the template content
            html_template_content = template.html_content
            plain_template_content = template.plain_text_content
            subject_template = template.subject or subject
            
            # Use Django's template engine for proper variable replacement
            html_template = Template(html_template_content)
            plain_template = Template(plain_template_content)
            subject_template_obj = Template(subject_template)
            
            # Create a context with our variables
            ctx = Context(context)
            
            # Render the templates
            html_content = html_template.render(ctx)
            plain_text_content = plain_template.render(ctx)
            subject = subject_template_obj.render(ctx)
            
            # Log that we're using the template
            logger.info(f"Using template {template.name} with variables: {context}")
        else:
            # Use simple plain text email
            plain_text_content = f"""
            This is a test email sent from {config.name}.
            
            Server: {context['server_name']}
            Time: {context['timestamp']}
            
            If you received this email, your email configuration is working correctly.
            """
            html_content = f"""
            <html>
            <body>
                <h2>Test Email from {config.name}</h2>
                <p>This is a test email sent from {config.name}.</p>
                <p><strong>Server:</strong> {context['server_name']}<br>
                <strong>Time:</strong> {context['timestamp']}</p>
                <p>If you received this email, your email configuration is working correctly.</p>
            </body>
            </html>
            """
            logger.info("No template found, using default test email content")
        
        # Record the email in history
        try:
            history = EmailHistory(
                email_type='test_email',
                recipient_email=to_email,
                subject=subject,
                body=plain_text_content,
                html_body=html_content,
                status="pending",
            )
            if template and hasattr(EmailHistory, 'template'):
                history.template = template
            history.save()
            logger.info(f"Created email history record for test email to {to_email}")
        except Exception as e:
            logger.error(f"Failed to save email history: {str(e)}")
            # Continue even if history saving fails
        
        # Try to send using SMTP first
        smtp_success = False
        smtp_error = None
        
        try:
            # First, verify we can resolve the hostname
            try:
                logger.info(f"Attempting to resolve hostname: {config.email_host}")
                socket.getaddrinfo(config.email_host, config.email_port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                logger.info(f"Successfully resolved {config.email_host}")
            except socket.gaierror as e:
                raise ConnectionError(f"Cannot resolve hostname '{config.email_host}'. Please check your email configuration. Error: {e}")
            
            # Use direct SMTP connection with SSL context for maximum reliability
            if config.email_use_ssl:
                # SSL connection
                logger.info(f"Establishing direct SMTP_SSL connection to {config.email_host}:{config.email_port}")
                smtp = smtplib.SMTP_SSL(
                    host=config.email_host, 
                    port=config.email_port, 
                    context=context_ssl,
                    timeout=30
                )
            else:
                # Regular connection, potentially with STARTTLS
                logger.info(f"Establishing direct SMTP connection to {config.email_host}:{config.email_port}")
                smtp = smtplib.SMTP(
                    host=config.email_host, 
                    port=config.email_port,
                    timeout=30
                )
                if config.email_use_tls:
                    logger.info("Starting TLS")
                    smtp.starttls(context=context_ssl)
            
            # Login
            logger.info(f"Logging in as {config.email_host_user}")
            smtp.login(config.email_host_user, config.email_host_password)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.default_from_email
            msg['To'] = to_email
            
            # Attach parts
            msg.attach(MIMEText(plain_text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send mail
            logger.info(f"Sending message to {to_email}")
            smtp.send_message(msg)
            smtp.quit()
            
            smtp_success = True
            logger.info(f"Test email sent successfully via SMTP to {to_email}")
        except Exception as e:
            smtp_error = str(e)
            logger.error(f"Failed to send test email via SMTP: {smtp_error}")
        
        # If SMTP failed, try using file-based backend as fallback for development
        if not smtp_success:
            try:
                logger.info("Trying file-based backend as fallback...")
                file_connection = get_connection(
                    backend='django.core.mail.backends.filebased.EmailBackend',
                    file_path='sent_emails',
                    fail_silently=False
                )
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_text_content,
                    from_email=config.default_from_email,
                    to=[to_email],
                    connection=file_connection
                )
                
                if html_content:
                    email.attach_alternative(html_content, "text/html")
                
                email.send()
                logger.info(f"Test email saved to file successfully (fallback method)")
                
                # Update history record
                try:
                    if 'history' in locals():
                        history.status = 'success'
                        history.save()
                except Exception as e:
                    logger.error(f"Failed to update email history: {str(e)}")
                
                template_info = f"using template '{template.name}'" if template else "with default text"
                return create_json_response({
                    'status': 'success', 
                    'message': f'Test email saved to file successfully (SMTP failed: {smtp_error})'
                })
            except Exception as file_error:
                logger.error(f"File-based email backend also failed: {str(file_error)}")
                
                # Update history record
                try:
                    if 'history' in locals():
                        history.status = 'failed'
                        history.error_message = f"SMTP: {smtp_error}, File: {str(file_error)}"
                        history.save()
                except Exception as hist_e:
                    logger.error(f"Failed to update email history with error: {str(hist_e)}")
                
                return create_json_response({
                    'status': 'error',
                    'message': f'Failed to send test email: {smtp_error}'
                }, 500)
        
        # If we got here, SMTP was successful
        # Update history record
        try:
            if 'history' in locals():
                history.status = 'success'
                history.save()
        except Exception as e:
            logger.error(f"Failed to update email history: {str(e)}")
        
        template_info = f"using template '{template.name}'" if template else "with default text"
        return create_json_response({
            'status': 'success', 
            'message': f'Test email sent successfully to {to_email} {template_info}'
        })
            
    except Exception as e:
        # Catch all other exceptions and return as JSON
        error_message = str(e)
        logger.error(f"Unexpected error in test_email_config: {error_message}", exc_info=True)
        return create_json_response({
            'status': 'error',
            'message': f'An unexpected error occurred: {error_message}'
        }, 500)

@staff_member_required
def debug_test_email(request, config_id):
    """
    Debug view that just returns a response without sending an email.
    This helps diagnose if the request is reaching the server.
    """
    logger.info(f"[DEBUG TEST] Debug test email request received for config_id: {config_id}")
    logger.info(f"[DEBUG TEST] Request method: {request.method}")
    logger.info(f"[DEBUG TEST] Request GET params: {request.GET}")
    logger.info(f"[DEBUG TEST] Request headers: {request.headers}")
    
    # Just return a success response for testing
    response = JsonResponse({
        'success': True,
        'message': 'Debug test received',
        'config_id': config_id,
        'recipient': request.GET.get('recipient', 'not specified')
    })
    
    # Add CORS headers
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    
    return response

def test_email_page(request):
    """
    A simple page to test the email sending functionality directly.
    """
    email_configs = EmailConfiguration.objects.all()
    
    return render(request, 'email_manager/test_email_page.html', {
        'email_configs': email_configs
    })

@login_required
@require_POST
def fetch_inbox_emails_view(request):
    """Manually fetch emails for a specific inbox"""
    inbox_id = request.POST.get('inbox_id')
    
    if not inbox_id:
        return JsonResponse({'status': 'error', 'message': 'No inbox specified'}, status=400)
    
    try:
        inbox = get_object_or_404(EmailInbox, pk=inbox_id, is_active=True)
        
        if not inbox.incoming_config:
            return JsonResponse({'status': 'error', 'message': 'No incoming mail configuration'}, status=400)
        
        if not inbox.incoming_config.is_active:
            return JsonResponse({'status': 'error', 'message': 'Incoming mail configuration is inactive'}, status=400)
        
        from .inbox_service import EmailFetchService
        service = EmailFetchService(inbox.incoming_config)
        count = service.fetch_emails(inbox)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully fetched {count} email(s)',
            'count': count
        })
        
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def send_email_view(request, pk):
    """Send an email message"""
    try:
        message = get_object_or_404(EmailMessage, pk=pk)
        
        if not message.inbox or not message.inbox.configuration:
            return JsonResponse({'status': 'error', 'message': 'No email configuration'}, status=400)
        
        # Get SMTP configuration
        config = message.inbox.configuration
        
        # Create email
        from django.core.mail import EmailMultiAlternatives
        from django.core.mail import get_connection
        
        connection = get_connection(
            host=config.email_host,
            port=config.email_port,
            username=config.email_host_user,
            password=config.email_host_password,
            use_tls=config.email_use_tls,
            use_ssl=config.email_use_ssl,
        )
        
        email = EmailMultiAlternatives(
            subject=message.subject,
            body=message.body,
            from_email=config.default_from_email,
            to=message.to_emails if isinstance(message.to_emails, list) else [message.to_emails],
            cc=message.cc_emails if message.cc_emails else [],
            bcc=message.bcc_emails if message.bcc_emails else [],
            connection=connection
        )
        
        if message.html_body:
            email.attach_alternative(message.html_body, "text/html")
        
        # Attach files
        for attachment in message.attachments.all():
            email.attach_file(attachment.file.path)
        
        # Send email
        email.send()
        
        # Update message status
        message.status = 'sent'
        message.sent_at = timezone.now()
        message.save()
        
        # Create email history record
        EmailHistory.objects.create(
            email_type='other',
            recipient_email=', '.join(message.to_emails) if isinstance(message.to_emails, list) else message.to_emails,
            subject=message.subject,
            body=message.body,
            html_body=message.html_body,
            status='success'
        )
        
        return JsonResponse({'status': 'success', 'message': 'Email sent successfully'})
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        
        # Update message status
        try:
            message.status = 'failed'
            message.save()
        except:
            pass
        
        # Create email history record
        try:
            EmailHistory.objects.create(
                email_type='other',
                recipient_email=', '.join(message.to_emails) if isinstance(message.to_emails, list) else message.to_emails,
                subject=message.subject,
                body=message.body,
                html_body=message.html_body,
                status='failed',
                error_message=str(e)
            )
        except:
            pass
        
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
