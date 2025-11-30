from django import forms
from .models import (
    EmailConfiguration,
    EmailTemplate,
    Newsletter,
    NewsletterSubscriber,
    EmailInbox,
    EmailMessage,
    EmailGuardian,
    EmailAutomation,
    EmailFolder,
    EmailLabel,
    EmailAttachment
)

class EmailConfigurationForm(forms.ModelForm):
    """Form for managing email configurations."""
    class Meta:
        model = EmailConfiguration
        fields = [
            'name',
            'email_host',
            'email_port',
            'email_host_user',
            'email_host_password',
            'email_use_tls',
            'email_use_ssl',
            'default_from_email',
            'is_default'
        ]
        widgets = {
            'email_host_password': forms.PasswordInput(render_value=True),
        }

class EmailTemplateForm(forms.ModelForm):
    """Form for managing email templates."""
    class Meta:
        model = EmailTemplate
        fields = [
            'name',
            'template_type',
            'subject',
            'html_content',
            'is_active'
        ]
        widgets = {
            'html_content': forms.Textarea(attrs={'class': 'tinymce'}),
        }

class NewsletterForm(forms.ModelForm):
    """Form for managing newsletters."""
    class Meta:
        model = Newsletter
        fields = [
            'title',
            'subject',
            'html_content',
            'plain_text_content',
            'template',
            'configuration',
            'scheduled_time',
            'status'
        ]
        widgets = {
            'html_content': forms.Textarea(attrs={'class': 'tinymce'}),
            'plain_text_content': forms.Textarea(attrs={'class': 'tinymce'}),
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class NewsletterSubscriberForm(forms.ModelForm):
    """Form for managing newsletter subscribers."""
    class Meta:
        model = NewsletterSubscriber
        fields = [
            'email',
            'name',
            'is_active'
        ]

class EmailInboxForm(forms.ModelForm):
    """Form for managing email inboxes."""
    class Meta:
        model = EmailInbox
        fields = ['name', 'email_address', 'configuration', 'is_active']

class EmailMessageForm(forms.ModelForm):
    """Form for managing email messages."""
    class Meta:
        model = EmailMessage
        fields = [
            'inbox', 'template', 'subject', 'body', 'html_body',
            'from_email', 'to_emails', 'cc_emails', 'bcc_emails',
            'priority'
        ]
        widgets = {
            'body': forms.Textarea(attrs={'class': 'tinymce'}),
            'html_body': forms.Textarea(attrs={'class': 'tinymce'}),
            'to_emails': forms.TextInput(attrs={'placeholder': 'Comma-separated email addresses'}),
            'cc_emails': forms.TextInput(attrs={'placeholder': 'Comma-separated email addresses'}),
            'bcc_emails': forms.TextInput(attrs={'placeholder': 'Comma-separated email addresses'}),
        }

class EmailGuardianForm(forms.ModelForm):
    """Form for managing email guardian rules."""
    class Meta:
        model = EmailGuardian
        fields = ['name', 'description', 'severity', 'rules', 'is_active']
        widgets = {
            'rules': forms.Textarea(attrs={'class': 'json-editor'}),
        }

class EmailAutomationForm(forms.ModelForm):
    """Form for managing email automation rules."""
    class Meta:
        model = EmailAutomation
        fields = [
            'name', 'description', 'trigger_type', 'trigger_conditions',
            'action_type', 'action_config', 'is_active'
        ]
        widgets = {
            'trigger_conditions': forms.Textarea(attrs={'class': 'json-editor'}),
            'action_config': forms.Textarea(attrs={'class': 'json-editor'}),
        }

class EmailFolderForm(forms.ModelForm):
    """Form for managing email folders."""
    class Meta:
        model = EmailFolder
        fields = ['name', 'description', 'parent_folder']

class EmailLabelForm(forms.ModelForm):
    """Form for managing email labels."""
    class Meta:
        model = EmailLabel
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class EmailAttachmentForm(forms.ModelForm):
    """Form for managing email attachments."""
    class Meta:
        model = EmailAttachment
        fields = ['file'] 