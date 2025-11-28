# accounts/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from .models import CustomUser, Company, BankDetail, CardDetail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import logging
import ssl
from django.utils import timezone
from django.conf import settings
# from email_manager.models import EmailConfiguration, EmailTemplate, EmailHistory
# from email_manager.utils import get_email_backend
from django.template import engines
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']  # Ensure the correct fields are listed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='form-control'),
            Field('email', css_class='form-control'),
            Field('password1', css_class='form-control'),
            Field('password2', css_class='form-control'),
            Submit('submit', 'Register', css_class='btn btn-primary w-100')
        )

# Custom user login form using crispy forms
class CustomUserLoginForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='form-control'),
            Field('password', css_class='form-control'),
            Submit('submit', 'Sign In', css_class='btn btn-success w-100')
        )
    
    def confirm_login_allowed(self, user):
        """
        Override to allow inactive users to log in.
        """
        # No restrictions - allow all users to log in regardless of is_active status
        pass


# Define the UserProfileForm to handle profile updates
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'fullname', 'gender', 'dob', 'phone', 'address', 'suburb', 'state', 'country']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})  # Apply Bootstrap styling


# Company creation form
class CompanyCreationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'owner_name', 'industry_type', 'employee_count', 'website', 'address', 'suburb', 'state', 'country', 'contact_email', 'logo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class BankDetailForm(forms.ModelForm):
    class Meta:
        model = BankDetail
        fields = ["bank_name", "account_number", "account_holder_name", "iban", "swift_code"]


class CardDetailForm(forms.ModelForm):
    class Meta:
        model = CardDetail
        fields = ["card_number", "cardholder_name", "expiry_date", "cvv"]

class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form that uses email configurations from the database."""
    
    def get_users(self, email):
        """
        Override the default get_users method to include inactive users.
        Given an email, return matching user(s) who should receive a reset.
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        email_field_name = User.get_email_field_name()
        
        # Modified to include ALL users with this email, even inactive ones
        active_users = User._default_manager.filter(
            **{
                f'{email_field_name}__iexact': email,
            }
        )
        
        # Log the query and results for debugging
        query = str(active_users.query)
        user_count = active_users.count()
        logger.info(f"Password reset search for email '{email}' found {user_count} users. Query: {query}")
        
        return (
            u for u in active_users
            if u.has_usable_password()
        )
    
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """Send password reset email using configured email settings."""
        # Log the attempt to send a password reset email
        logger.info(f"Attempting to send password reset email to {to_email}")
        
        # Try to find a configuration specifically for password reset emails
        try:
            # First, try to find a configuration with "Password Reset Emails" exact name
            config = EmailConfiguration.objects.filter(name="Password Reset Emails").first()
            
            if not config:
                # Next, try to find a configuration containing "Password Reset" in the name
                config = EmailConfiguration.objects.filter(name__icontains="Password Reset").first()
                
            if not config:
                # As a last resort, fall back to the default configuration
                config = EmailConfiguration.objects.filter(is_default=True).first()
                
            if config:
                logger.info(f"Using email configuration: {config.name} (ID: {config.id}) - Host: {config.email_host}, Port: {config.email_port}")
                logger.info(f"Email user: {config.email_host_user}, TLS: {config.email_use_tls}, SSL: {config.email_use_ssl}")
            else:
                logger.warning("No email configuration found, will use Django's default settings")
            
        except Exception as e:
            logger.error(f"Error finding email configuration: {str(e)}")
            config = None
        
        # Use the configuration's default from_email if none is provided
        if not from_email and config and config.default_from_email:
            from_email = config.default_from_email
        
        # Make sure we have a from_email
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
            
        logger.info(f"Using from_email: {from_email}")
        
        # Try to find a template specifically for password reset
        try:
            template = EmailTemplate.objects.filter(name="password_reset").first()
            if template:
                logger.info(f"Using email template: {template.name} (ID: {template.id})")
                
                # Use the template from the database
                html_content = template.html_content
                plain_content = template.plain_text_content
                
                # Prepare context for template rendering
                user_list = list(self.get_users(to_email))
                user_model = user_list[0] if user_list else None
                
                if user_model:
                    # Get uid and token
                    uid = urlsafe_base64_encode(force_bytes(user_model.pk))
                    token = default_token_generator.make_token(user_model)
                    
                    email_context = {
                        'full_name': user_model.get_full_name() if hasattr(user_model, 'get_full_name') else user_model.username,
                        'username': user_model.username,
                        'email': user_model.email,
                        'domain': context.get('domain'),
                        'site_name': context.get('site_name'),
                        'protocol': context.get('protocol', 'https'),
                        'uid': uid,
                        'token': token,
                        'reset_url': f"{context.get('protocol', 'https')}://{context.get('domain')}/accounts/reset/{uid}/{token}/",
                        'date': timezone.now().strftime("%B %d, %Y"),
                        'app_name': 'MyComparables'
                    }
                    
                    logger.info(f"Prepared email context with reset URL: {email_context.get('reset_url')}")
                    
                    # Use Django's Template engine for proper variable substitution
                    from django.template import Template, Context
                    template_html = Template(html_content)
                    template_plain = Template(plain_content)
                    
                    html_email = template_html.render(Context(email_context))
                    body = template_plain.render(Context(email_context))
                    
                    # Override the subject with the template's subject
                    subject = template.subject
                else:
                    logger.warning(f"No user found with email {to_email}, using standard templates")
                    # Fallback to standard templates
                    subject = self._render_template(subject_template_name, context)
                    body = self._render_template(email_template_name, context)
                    if html_email_template_name:
                        html_email = self._render_template(html_email_template_name, context)
                    else:
                        html_email = None
            else:
                # Use standard templates
                subject = self._render_template(subject_template_name, context)
                body = self._render_template(email_template_name, context)
                if html_email_template_name:
                    html_email = self._render_template(html_email_template_name, context)
                else:
                    html_email = None
                    
        except Exception as e:
            logger.error(f"Error with email template: {str(e)}", exc_info=True)
            # Use standard templates as fallback
            subject = self._render_template(subject_template_name, context)
            body = self._render_template(email_template_name, context)
            if html_email_template_name:
                html_email = self._render_template(html_email_template_name, context)
            else:
                html_email = None
            
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        
        # Log email content for debugging
        logger.info(f"Email subject: {subject}")
        logger.info(f"Email body length: {len(body)}")
        if html_email:
            logger.info(f"HTML email length: {len(html_email)}")
        
        # Create a special SSL context for development environments
        if settings.DEBUG:
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = None
        
        # Get the connection using our configured email settings
        connection = None
        if config:
            try:
                connection = get_email_backend(config=config)
                logger.info(f"Email backend created with configuration {config.name}")
            except Exception as e:
                logger.error(f"Error creating email backend: {str(e)}", exc_info=True)
        
        # Create the email message
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
            connection=connection,
        )
        
        # Attach HTML version if available
        if html_email:
            email_message.attach_alternative(html_email, "text/html")
        
        # Create history record
        try:
            history = EmailHistory(
                recipient_email=to_email,
                email_type="password_reset",
                subject=subject,
                body=body,
                status='pending'  # Will be updated after sending attempt
            )
            history.save()
            
        except Exception as e:
            logger.error(f"Error creating email history: {str(e)}", exc_info=True)
            history = None
        
        # Try to send the email and update history
        try:
            # Send the email
            sent = email_message.send()
            logger.info(f"Email send attempt result: {sent}")
            
            # Log success
            logger.info(f"Password reset email sent successfully to {to_email}")
            
            # Update history record with success
            if history:
                history.status = "success"
                history.save()
            
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to send password reset email to {to_email}: {error_message}", exc_info=True)
            
            # Update history record with failure
            if history:
                history.status = "failed"
                history.error_message = error_message
                history.save()
            
            # Print for local development
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
            
            # Try with Django's default email settings as a fallback
            try:
                logger.info("Attempting to send with Django's default email settings")
                # Create a new email message with default connection
                default_email = EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[to_email],
                )
                
                if html_email:
                    default_email.attach_alternative(html_email, "text/html")
                
                # Send with default settings
                sent = default_email.send()
                logger.info(f"Default email send attempt result: {sent}")
                
                # Log success of fallback method
                logger.info(f"Password reset email sent successfully with default settings to {to_email}")
                
                # Update history record
                if history:
                    history.status = "success"
                    history.notes = "Sent using Django default email settings"
                    history.save()
                
                return True
                
            except Exception as fallback_error:
                logger.error(f"Fallback email attempt also failed: {str(fallback_error)}", exc_info=True)
                
                # Update history with additional failure information
                if history:
                    history.error_message = f"{error_message}\nFallback error: {str(fallback_error)}"
                    history.save()
                
                # For development, show direct activation option
                if settings.DEBUG:
                    user_list = list(self.get_users(to_email))
                    if user_list:
                        user = user_list[0]
                        uid = urlsafe_base64_encode(force_bytes(user.pk))
                        token = default_token_generator.make_token(user)
                        reset_url = f"/accounts/reset/{uid}/{token}/"
                        logger.info(f"DEBUG MODE: Direct password reset URL: {reset_url}")
                
                # Raise the original error to be handled by the view
                raise Exception(f"Failed to send password reset email: {error_message}") from e
    
    def _render_template(self, template_name, context):
        """Render a template with the given context."""
        try:
            template_engine = engines['django']
            template = template_engine.get_template(template_name)
            return template.render(context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}", exc_info=True)
            return f"Error rendering template: {str(e)}"