from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import secrets
import re
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone

class EmailConfiguration(models.Model):
    name = models.CharField(max_length=100, help_text='A name to identify this email configuration')
    email_host = models.CharField(max_length=255, help_text='SMTP server address (e.g., smtp.gmail.com)')
    email_port = models.PositiveIntegerField(help_text='SMTP server port (e.g., 587 for TLS, 465 for SSL)')
    email_host_user = models.EmailField(help_text='Email address to send from')
    email_host_password = models.CharField(max_length=255, help_text='Password or app password for the email account')
    email_use_tls = models.BooleanField(default=True, help_text='Use TLS encryption')
    email_use_ssl = models.BooleanField(default=False, help_text='Use SSL encryption (do not enable both TLS and SSL)')
    default_from_email = models.EmailField(help_text='Default sender email address (can be same as host user)')
    is_default = models.BooleanField(default=False, help_text='Use this configuration as the default for the site')
    test_email = models.EmailField(blank=True, null=True, help_text='Email address to send test emails to')
    default_template_id = models.IntegerField(blank=True, null=True, help_text='Default template ID to use for this config')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Config'
        verbose_name_plural = 'Email Config'
    
    def __str__(self):
        return f"{self.name} ({self.email_host_user})"
    
    @property
    def default_template(self):
        """
        Get the default template for this configuration
        """
        if not self.default_template_id:
            return None
        
        try:
            from .models import EmailTemplate
            return EmailTemplate.objects.get(pk=self.default_template_id)
        except Exception:
            return None
            
    @default_template.setter
    def default_template(self, template):
        """
        Set the default template for this configuration
        """
        if template is None:
            self.default_template_id = None
        else:
            self.default_template_id = template.id
    
    def save(self, *args, **kwargs):
        # If this config is being set as default, unset any other defaults
        if self.is_default:
            EmailConfiguration.objects.filter(is_default=True).update(is_default=False)
        # If no configs exist yet, make this one the default
        elif not self.pk and not EmailConfiguration.objects.exists():
            self.is_default = True
        # If this is the only config, make it the default
        elif EmailConfiguration.objects.count() == 0:
            self.is_default = True
        super().save(*args, **kwargs)
        
    @classmethod
    def get_default(cls):
        """Get the default email configuration"""
        default_config = cls.objects.filter(is_default=True).first()
        if not default_config:
            # If no default is set, try to get the first available configuration
            default_config = cls.objects.first()
        return default_config

class IncomingMailConfiguration(models.Model):
    """Model for IMAP/POP3 configuration to receive emails"""
    PROTOCOL_CHOICES = [
        ('imap', 'IMAP'),
        ('pop3', 'POP3'),
    ]
    
    SECURITY_CHOICES = [
        ('none', 'None'),
        ('ssl', 'SSL/TLS'),
        ('starttls', 'STARTTLS'),
    ]
    
    AUTH_CHOICES = [
        ('password', 'Normal Password'),
        ('oauth2', 'OAuth2'),
    ]
    
    name = models.CharField(max_length=100, help_text='A name to identify this incoming mail configuration')
    protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default='imap', help_text='Mail protocol (IMAP or POP3)')
    email_address = models.EmailField(help_text='Email address to fetch mail from')
    
    # Server settings
    mail_server = models.CharField(max_length=255, help_text='Mail server address (e.g., imap.gmail.com, imap.endevops.com)')
    mail_port = models.PositiveIntegerField(help_text='Mail server port (e.g., 993 for IMAP SSL, 143 for IMAP STARTTLS, 995 for POP3 SSL)')
    
    # Authentication
    username = models.CharField(max_length=255, help_text='Username for authentication (usually email address)')
    password = models.CharField(max_length=255, help_text='Password or app password')
    auth_method = models.CharField(max_length=20, choices=AUTH_CHOICES, default='password', help_text='Authentication method')
    
    # Security
    connection_security = models.CharField(max_length=20, choices=SECURITY_CHOICES, default='starttls', help_text='Connection security method')
    
    # Fetch settings
    auto_fetch = models.BooleanField(default=True, help_text='Automatically fetch new messages')
    fetch_interval = models.PositiveIntegerField(default=10, help_text='Fetch interval in minutes')
    fetch_on_startup = models.BooleanField(default=True, help_text='Check for new messages at startup')
    
    # Folder settings
    inbox_folder = models.CharField(max_length=100, default='INBOX', help_text='IMAP folder to fetch from')
    trash_folder = models.CharField(max_length=100, default='Trash', help_text='Trash folder name', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, help_text='Whether this configuration is active')
    last_fetched = models.DateTimeField(null=True, blank=True, help_text='Last time emails were fetched')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Incoming Mail Config'
        verbose_name_plural = 'Incoming Mail Configs'
    
    def __str__(self):
        return f"{self.name} ({self.email_address}) - {self.protocol.upper()}"

class EmailHistory(models.Model):
    EMAIL_TYPES = [
        ('contact_form', 'Contact Form Notification'),
        ('appointment_request', 'Appointment Request'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('test_email', 'Test Email Configuration'),
        ('newsletter', 'Newsletter'),
        ('scheduled_email', 'Scheduled Email'),
        ('other', 'Other'),
    ]

    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    html_body = models.TextField(blank=True, null=True, help_text="HTML version of the email body")
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
    ])
    error_message = models.TextField(blank=True, null=True)
    
    # Generic foreign key to link to the related object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_manager_history'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Email History'
        verbose_name_plural = 'Email History'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['email_type']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['recipient_email']),
        ]

    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"

class EmailTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('contact_form', 'Contact Form Notification'),
        ('appointment_request', 'Appointment Request'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('newsletter', 'Newsletter'),
        ('welcome', 'Welcome Email'),
        ('file_share', 'File Share'),
        ('folder_share', 'Folder Share'),
        ('custom', 'Custom Email'),
    ]
    
    name = models.CharField(max_length=100, help_text="Template name for easy identification")
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, default='custom')
    subject = models.CharField(max_length=255, help_text="Email subject line")
    html_content = models.TextField(help_text="HTML content of the email")
    plain_text_content = models.TextField(help_text="Plain text version of the email")
    configuration = models.ForeignKey(
        EmailConfiguration, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Email configuration to use for sending this template. If blank, default configuration will be used."
    )
    variables = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="List of variables used in the template, with examples. E.g. {'name': 'John', 'date': '2023-01-01'}"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this template is active and can be used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

    @classmethod
    def update_file_share_template(cls):
        """Update the file_share template to support large file download links"""
        try:
            template = cls.objects.get(name='file_share')
            
            # Update the HTML content to support download links
            html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>File Shared with You</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
        .container { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #0061f2 0%, #00c6f9 100%); color: white; padding: 25px; text-align: center; }
        .content { padding: 30px; background-color: white; }
        .file-info { background-color: #f7f9fc; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0061f2; }
        .download-button { display: inline-block; background-color: #0061f2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 30px; font-weight: 600; margin-top: 15px; text-align: center; }
        .download-button:hover { background-color: #0052cc; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #f7f9fc; color: #666; font-size: 12px; border-top: 1px solid #eaeaea; }
        .logo { width: 120px; height: auto; margin-bottom: 15px; }
        .expire-notice { font-size: 12px; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>File Shared with You</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p><strong>{{ shared_by }}</strong> has shared a file with you.</p>

            <div class="file-info">
                <p><strong>File Name:</strong> {{ file_name }}</p>
                <p><strong>File Type:</strong> {{ file_type }}</p>
                <p><strong>File Size:</strong> {{ file_size }}</p>
                <p><strong>Shared By:</strong> {{ shared_by }} ({{ sender_email }})</p>
                {% if message %}
                <p><strong>Message:</strong> {{ message }}</p>
                {% endif %}
            </div>

            {% if is_large_file %}
            <p>This file is too large to attach directly to this email.</p>
            <p>Please use the secure download link below to access the file:</p>
            <div style="text-align: center;">
                <a href="{{ download_link }}" class="download-button">Download File</a>
                <p class="expire-notice">This download link will expire in {{ expiration_time }}.</p>
            </div>
            {% else %}
            <p>The file has been attached to this email for your convenience.</p>
            {% endif %}

            <p>Thank you for using our service!</p>
        </div>
        <div class="footer">
            <p>This is an automated message.</p>
            <p>&copy; 2024 {{ site_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
            
            # Also update the plain text content
            plain_text_content = """
File Shared with You

Hello,

{{ shared_by }} has shared a file with you.

File Name: {{ file_name }}
File Type: {{ file_type }}
File Size: {{ file_size }}
Shared By: {{ shared_by }} ({{ sender_email }})
{% if message %}Message: {{ message }}{% endif %}

{% if is_large_file %}
This file is too large to attach directly to this email.
Please use the secure download link below to access the file:

{{ download_link }}

This download link will expire in {{ expiration_time }}.
{% else %}
The file has been attached to this email for your convenience.
{% endif %}

Thank you for using our service!

--
This is an automated message.
© 2024 {{ site_name }}. All rights reserved.
"""
            
            # Update the template
            template.html_content = html_content
            template.plain_text_content = plain_text_content
            template.save()
            
            return template
            
        except cls.DoesNotExist:
            # Create the template if it doesn't exist
            return cls.objects.create(
                name='file_share',
                subject='File Shared with You',
                template_type='file_share',
                html_content=html_content,
                plain_text_content=plain_text_content,
                is_active=True
            )

class ScheduledEmail(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    template = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.CASCADE,
        related_name='scheduled_emails',
        help_text="Email template to use"
    )
    configuration = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_emails',
        help_text="Specific email configuration to use. If blank, the template's configuration or system default will be used."
    )
    subject_override = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Override the template subject (optional)"
    )
    recipients = models.JSONField(help_text="List of email addresses to send to")
    variables_data = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Variables to replace in the template. E.g. {'name': 'John', 'date': '2023-01-01'}"
    )
    scheduled_time = models.DateTimeField(help_text="When to send this email")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_time = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0, help_text="Number of attempts to send this email")
    last_attempt = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_manager_scheduled_emails'
    )
    
    class Meta:
        verbose_name = 'Scheduled Email'
        verbose_name_plural = 'Scheduled Emails'
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_time']),
        ]
    
    def __str__(self):
        return f"{self.template.name} scheduled for {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"

class Newsletter(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200, help_text="Newsletter title")
    subject = models.CharField(max_length=255, help_text="Email subject line")
    html_content = models.TextField(help_text="HTML content of the newsletter")
    plain_text_content = models.TextField(help_text="Plain text version of the newsletter")
    template = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='newsletters',
        help_text="Template to use for this newsletter (optional)"
    )
    configuration = models.ForeignKey(
        EmailConfiguration, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Email configuration to use. If blank, default configuration will be used."
    )
    scheduled_time = models.DateTimeField(null=True, blank=True, help_text="When to send this newsletter")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_time = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    successful_sends = models.PositiveIntegerField(default=0)
    failed_sends = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_manager_newsletters'
    )
    
    class Meta:
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50, default='website')
    token = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sent_newsletter = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.email} ({'Confirmed' if self.confirmed else 'Unconfirmed'})"
    
    def generate_token(self):
        """Generate a secure token for subscription confirmation"""
        self.token = secrets.token_urlsafe(32)
        return self.token
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['confirmed']),
        ]

class EmailInbox(models.Model):
    """Model for managing email inboxes."""
    name = models.CharField(max_length=100)
    email_address = models.EmailField(unique=True)
    description = models.TextField(blank=True, null=True, help_text='Description of this inbox')
    
    # Outgoing mail configuration (SMTP)
    configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE, related_name='outgoing_inboxes', help_text='SMTP configuration for sending emails')
    
    # Incoming mail configuration (IMAP/POP3)
    incoming_config = models.ForeignKey(IncomingMailConfiguration, on_delete=models.SET_NULL, null=True, blank=True, related_name='inboxes', help_text='IMAP/POP3 configuration for receiving emails')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Inbox'
        verbose_name_plural = 'Email Inboxes'
    
    def __str__(self):
        return f"{self.name} ({self.email_address})"

class EmailMessage(models.Model):
    """Model for storing email messages."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    inbox = models.ForeignKey(EmailInbox, on_delete=models.CASCADE, related_name='messages')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Message identifiers
    message_id = models.CharField(max_length=255, blank=True, null=True, help_text='Unique message ID from email server')
    uid = models.CharField(max_length=100, blank=True, null=True, help_text='UID from IMAP server')
    
    subject = models.CharField(max_length=255)
    body = models.TextField()
    html_body = models.TextField(blank=True, null=True)
    raw_content = models.TextField(blank=True, null=True, help_text='Raw email content')
    
    from_email = models.EmailField()
    to_emails = models.JSONField()  # List of recipient email addresses
    cc_emails = models.JSONField(default=list, blank=True)  # List of CC email addresses
    bcc_emails = models.JSONField(default=list, blank=True)  # List of BCC email addresses
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    is_favorite = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    is_forwarded = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Email Message'
        verbose_name_plural = 'Email Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_favorite']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"

class EmailAttachment(models.Model):
    """Model for email attachments."""
    message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='email_attachments/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Email Attachment'
        verbose_name_plural = 'Email Attachments'
    
    def __str__(self):
        return f"{self.filename} ({self.message.subject})"

class EmailGuardian(models.Model):
    """Model for email security and monitoring."""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    rules = models.JSONField(help_text="JSON configuration for security rules")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Guardian'
        verbose_name_plural = 'Email Guardians'
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"

class SecurityAlert(models.Model):
    """Model for security alerts and notifications."""
    ALERT_TYPES = [
        ('suspicious', 'Suspicious Activity'),
        ('fraud', 'Potential Fraud'),
        ('sensitive', 'Sensitive Content'),
        ('spam', 'Spam Detection'),
        ('malware', 'Malware Detection'),
    ]
    
    guardian = models.ForeignKey(EmailGuardian, on_delete=models.CASCADE)
    message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Security Alert'
        verbose_name_plural = 'Security Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.message.subject}"

class EmailAutomation(models.Model):
    """Model for email automation rules."""
    TRIGGER_TYPES = [
        ('received', 'Email Received'),
        ('sent', 'Email Sent'),
        ('attachment', 'Attachment Detected'),
        ('keyword', 'Keyword Detected'),
        ('schedule', 'Scheduled'),
    ]
    
    ACTION_TYPES = [
        ('forward', 'Forward Email'),
        ('reply', 'Auto Reply'),
        ('move', 'Move to Folder'),
        ('label', 'Apply Label'),
        ('notify', 'Send Notification'),
        ('archive', 'Archive Email'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_conditions = models.JSONField(help_text="JSON configuration for trigger conditions")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_config = models.JSONField(help_text="JSON configuration for action parameters")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Automation'
        verbose_name_plural = 'Email Automations'
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()} → {self.get_action_type_display()})"

class EmailFolder(models.Model):
    """Model for organizing email messages into folders."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Email Folder'
        verbose_name_plural = 'Email Folders'
    
    def __str__(self):
        return self.name

class EmailLabel(models.Model):
    """Model for labeling email messages."""
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, validators=[RegexValidator(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')])
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Email Label'
        verbose_name_plural = 'Email Labels'
    
    def __str__(self):
        return self.name

class MessageLabel(models.Model):
    """Model for associating labels with messages."""
    message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE)
    label = models.ForeignKey(EmailLabel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Message Label'
        verbose_name_plural = 'Message Labels'
        unique_together = ['message', 'label']
    
    def __str__(self):
        return f"{self.label.name} on {self.message.subject}"

class EmailGuardianRule(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    pattern = models.TextField(help_text="Regex pattern to match against email content")
    action = models.CharField(max_length=50, choices=[
        ('quarantine', 'Quarantine'),
        ('delete', 'Delete'),
        ('mark_spam', 'Mark as Spam'),
        ('notify', 'Notify Admin'),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.severity})"

class EmailScanResult(models.Model):
    email = models.ForeignKey('EmailMessage', on_delete=models.CASCADE)
    guardian_rule = models.ForeignKey(EmailGuardianRule, on_delete=models.CASCADE)
    scan_date = models.DateTimeField(auto_now_add=True)
    matched_content = models.TextField()
    action_taken = models.CharField(max_length=50)
    details = models.JSONField(default=dict)

    def __str__(self):
        return f"Scan for {self.email.subject} - {self.guardian_rule.name}"

class DeviceScript(models.Model):
    OS_CHOICES = [
        ('windows', 'Windows'),
        ('linux', 'Linux'),
        ('macos', 'macOS'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    operating_system = models.CharField(max_length=10, choices=OS_CHOICES)
    script_content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.operating_system})"

class Device(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]

    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=100, unique=True)
    operating_system = models.CharField(max_length=10, choices=DeviceScript.OS_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_seen = models.DateTimeField(auto_now=True)
    security_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    installed_scripts = models.ManyToManyField(DeviceScript, through='DeviceScriptExecution')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.device_id})"

class DeviceScriptExecution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    script = models.ForeignKey(DeviceScript, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.device.name} - {self.script.name}"

    def complete(self, output=None, error=None):
        self.status = 'completed' if not error else 'failed'
        self.completion_date = timezone.now()
        if output:
            self.output = output
        if error:
            self.error_message = error
        self.save()
