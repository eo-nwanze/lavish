# accounts/tools.py

import pyotp
import qrcode
from io import BytesIO
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.base import ContentFile
import logging
import socket
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
import datetime
import re
import base64
import ssl

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Function to generate TOTP secret
def generate_totp_secret():
    """Generate a new TOTP secret for MFA"""
    return pyotp.random_base32()

# Function to generate QR code for TOTP
def generate_totp_qr_code(secret, username, issuer_name="Vx_Manager"):
    """Generate QR code for the TOTP secret"""
    try:
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer_name)
        
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, returning URI only for manual entry")
            return None, uri
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert PIL image to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Convert to base64 for display in template
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_base64, uri
    except Exception as e:
        logger.error(f"Failed to generate QR code: {str(e)}")
        return None, None

# Function to verify OTP
def verify_otp(secret, otp):
    """Verify the OTP code provided by the user"""
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(otp)
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return False

# Function to send a welcome email with verification link
def send_verification_email(user, request):
    try:
        # Generate a verification link
        current_site = get_current_site(request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = f"http://{current_site.domain}/accounts/activate/{uid}/{token}/"
        
        # Create a simple email message
        mail_subject = 'Activate your VX Manager account'
        message = f'''
        Hello {user.username},
        
        Thank you for registering with VX Manager! Please click the link below to verify your email:
        {verify_url}
        
        If you didn't register for an account, please ignore this email.
        
        Best regards,
        The VX Management Team
        '''
        
        # Attempt to send the email
        send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])
        return True, "Verification email sent successfully"
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        # If in development, return activation link
        if settings.DEBUG:
            return False, f"Email sending failed, but you can activate your account by visiting: {verify_url}"
        return False, "Email sending failed. Please contact support."

# Function to send login notification email
def send_login_notification(user, request):
    try:
        # Get user's IP address and device info
        ip = request.META.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Try to get a location based on IP (mock for now)
        location = "Unknown"
        
        # Get current time in user's timezone if available
        login_time = timezone.now()
        
        # Prepare context for the email template
        context = {
            'username': user.username,
            'email': user.email,
            'login_time': login_time.strftime("%Y-%m-%d %H:%M:%S"),
            'ip_address': ip,
            'device': user_agent,
            'location': location,
            'year': timezone.now().year,
            'company_name': 'EndevOps Inc.',
            'site_name': 'EndevOps',
        }
        
        # Try to use the email_manager's template system first
        try:
            from email_manager.models import EmailConfiguration, EmailTemplate, EmailHistory
            from email_manager.utils import get_email_backend_email
            
            # Send using the login_notification template
            result = send_template_email(
                template_name='login_notification',
                recipient_list=[user.email],
                email_type='login_notification',
                related_object=user
            )
            
            if result:
                return True, "Login notification sent using template"
            else:
                # Fall back to basic email if template sending failed
                raise Exception("Template email sending failed")
                
        except Exception as template_error:
            logger.warning(f"Template email failed, falling back to basic email: {str(template_error)}")
            
            # Create a simple notification message as fallback
            mail_subject = 'New login to your VX-Manager account'
            message = f'''
            Hello {user.username},
            
            We detected a new login to your EndevOps account.
            
            Time: {login_time.strftime("%Y-%m-%d %H:%M:%S")}
            IP Address: {ip}
            Device: {user_agent}
            
            If this was you, you can ignore this message. If you didn't log in, please 
            secure your account immediately by changing your password.
            
            Best regards,
            The EndevOps Team
            '''
            
            # Send the notification using basic Django mail
            from django.core.mail import send_mail
            send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])
            return True, "Login notification sent using basic email"
            
    except Exception as e:
        logger.error(f"Failed to send login notification: {str(e)}", exc_info=True)
        return False, f"Failed to send login notification: {str(e)}" 