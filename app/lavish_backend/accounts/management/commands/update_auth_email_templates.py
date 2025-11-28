from django.core.management.base import BaseCommand
from django.utils import timezone
from email_manager.models import EmailTemplate, EmailConfiguration
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ensure all required authentication email templates exist in the system'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Checking and updating authentication email templates..."))
        
        # Get default email configuration
        config = EmailConfiguration.objects.filter(is_default=True).first()
        if not config:
            self.stdout.write(self.style.WARNING("No default email configuration found. Templates will be created without configuration."))
        
        # Check and create templates
        templates_created = 0
        templates_updated = 0
        
        # Welcome Email
        welcome_email = self.get_or_create_template(
            name='welcome_email',
            subject='Welcome to EndevOps!',
            template_type='welcome',
            html_content=self.get_welcome_email_html(),
            plain_text_content=self.get_welcome_email_text(),
            config=config
        )
        if welcome_email[1]:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f"Created welcome_email template"))
        else:
            templates_updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated welcome_email template"))
        
        # Account Activation
        account_activation = self.get_or_create_template(
            name='account_activation',
            subject='Activate Your EndevOps Account',
            template_type='custom',
            html_content=self.get_account_activation_html(),
            plain_text_content=self.get_account_activation_text(),
            config=config
        )
        if account_activation[1]:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f"Created account_activation template"))
        else:
            templates_updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated account_activation template"))
        
        # Login Notification
        login_notification = self.get_or_create_template(
            name='login_notification',
            subject='New Login to Your EndevOps Account',
            template_type='custom',
            html_content=self.get_login_notification_html(),
            plain_text_content=self.get_login_notification_text(),
            config=config
        )
        if login_notification[1]:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f"Created login_notification template"))
        else:
            templates_updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated login_notification template"))
        
        # Password Reset
        password_reset = self.get_or_create_template(
            name='password_reset',
            subject='Reset Your EndevOps Password',
            template_type='custom',
            html_content=self.get_password_reset_html(),
            plain_text_content=self.get_password_reset_text(),
            config=config
        )
        if password_reset[1]:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f"Created password_reset template"))
        else:
            templates_updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated password_reset template"))
        
        # Final summary
        self.stdout.write(self.style.SUCCESS(f"Authentication email templates updated: {templates_created} created, {templates_updated} updated"))
    
    def get_or_create_template(self, name, subject, template_type, html_content, plain_text_content, config=None):
        """Get or create an email template, updating it if it exists"""
        try:
            template, created = EmailTemplate.objects.update_or_create(
                name=name,
                defaults={
                    'subject': subject,
                    'template_type': template_type,
                    'html_content': html_content,
                    'plain_text_content': plain_text_content,
                    'configuration': config,
                    'is_active': True,
                    'variables': self.get_template_variables(name),
                }
            )
            return template, created
        except Exception as e:
            logger.error(f"Error creating/updating template {name}: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error creating/updating template {name}: {str(e)}"))
            return None, False
    
    def get_template_variables(self, template_name):
        """Get the variables for each template type"""
        common_vars = {
            'username': 'john_doe',
            'email': 'user@example.com',
            'site_name': 'EndevOps',
            'site_url': 'https://example.com',
            'app_name': 'EndevOps',
            'company_name': 'EndevOps Inc.',
            'year': timezone.now().year,
        }
        
        template_specific = {
            'welcome_email': {},
            'account_activation': {
                'activation_link': 'https://example.com/activate/token/',
                'activation_token': 'sample-token',
                'uid': 'sample-uid',
            },
            'login_notification': {
                'login_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': '192.168.1.1',
                'device': 'Windows 10 / Chrome',
                'location': 'Sydney, Australia',
            },
            'password_reset': {
                'reset_link': 'https://example.com/reset/token/',
                'reset_token': 'sample-token',
                'uid': 'sample-uid',
                'token': 'sample-token',
                'reset_url': 'https://example.com/reset/sample-uid/sample-token/',
            },
        }
        
        return {**common_vars, **(template_specific.get(template_name, {}))}
    
    # Template HTML content
    def get_welcome_email_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to EndevOps</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
                .container { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #0061f2 0%, #00c6f9 100%); color: white; padding: 25px; text-align: center; }
                .content { padding: 30px; background-color: white; }
                .button { display: inline-block; background-color: #0061f2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 15px; }
                .button:hover { background-color: #0052cc; }
                .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #f7f9fc; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to EndevOps!</h1>
                </div>
                <div class="content">
                    <p>Hello {{ username }},</p>
                    <p>Welcome to EndevOps! We're excited to have you on board.</p>
                    <p>Your account has been created successfully with the email address <strong>{{ email }}</strong>.</p>
                    <p>With EndevOps, you can:</p>
                    <ul>
                        <li>Manage your projects efficiently</li>
                        <li>Collaborate with team members</li>
                        <li>Monitor and analyze your processes</li>
                        <li>And much more!</li>
                    </ul>
                    <p>Get started by exploring our dashboard:</p>
                    <p style="text-align: center;">
                        <a href="{{ site_url }}" class="button">Go to Dashboard</a>
                    </p>
                    <p>If you have any questions or need assistance, feel free to contact our support team.</p>
                    <p>Best regards,<br>The EndevOps Team</p>
                </div>
                <div class="footer">
                    <p>© {{ year }} {{ company_name }}. All rights reserved.</p>
                    <p>This email was sent to {{ email }}</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_welcome_email_text(self):
        return '''
Welcome to EndevOps!

Hello {{ username }},

Welcome to EndevOps! We're excited to have you on board.

Your account has been created successfully with the email address {{ email }}.

With EndevOps, you can:
- Manage your projects efficiently
- Collaborate with team members
- Monitor and analyze your processes
- And much more!

Get started by exploring our dashboard: {{ site_url }}

If you have any questions or need assistance, feel free to contact our support team.

Best regards,
The EndevOps Team

© {{ year }} {{ company_name }}. All rights reserved.
This email was sent to {{ email }}
        '''
    
    def get_account_activation_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Activate Your EndevOps Account</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
                .container { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #0061f2 0%, #00c6f9 100%); color: white; padding: 25px; text-align: center; }
                .content { padding: 30px; background-color: white; }
                .button { display: inline-block; background-color: #0061f2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 15px; }
                .button:hover { background-color: #0052cc; }
                .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #f7f9fc; color: #666; font-size: 12px; }
                .note { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0061f2; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Activate Your Account</h1>
                </div>
                <div class="content">
                    <p>Hello {{ username }},</p>
                    <p>Thank you for registering with EndevOps! To complete your registration and activate your account, please click the button below:</p>
                    <p style="text-align: center;">
                        <a href="{{ activation_link }}" class="button">Activate Account</a>
                    </p>
                    <div class="note">
                        <p>If the button above doesn't work, you can also copy and paste the following link into your browser:</p>
                        <p>{{ activation_link }}</p>
                    </div>
                    <p>This activation link will expire in 24 hours. If you did not sign up for an EndevOps account, please ignore this email.</p>
                    <p>Best regards,<br>The EndevOps Team</p>
                </div>
                <div class="footer">
                    <p>© {{ year }} {{ company_name }}. All rights reserved.</p>
                    <p>This email was sent to {{ email }}</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_account_activation_text(self):
        return '''
Activate Your EndevOps Account

Hello {{ username }},

Thank you for registering with EndevOps! To complete your registration and activate your account, please click on the link below:

{{ activation_link }}

This activation link will expire in 24 hours.

If you did not sign up for an EndevOps account, please ignore this email.

Best regards,
The EndevOps Team

© {{ year }} {{ company_name }}. All rights reserved.
This email was sent to {{ email }}
        '''
    
    def get_login_notification_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New Login to Your EndevOps Account</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
                .container { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #0061f2 0%, #00c6f9 100%); color: white; padding: 25px; text-align: center; }
                .content { padding: 30px; background-color: white; }
                .button { display: inline-block; background-color: #0061f2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 15px; }
                .button:hover { background-color: #0052cc; }
                .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #f7f9fc; color: #666; font-size: 12px; }
                .alert { background-color: #fff8f8; padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0; }
                .details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Login Detected</h1>
                </div>
                <div class="content">
                    <p>Hello {{ username }},</p>
                    <p>We detected a new login to your EndevOps account. Here are the details:</p>
                    
                    <div class="details">
                        <p><strong>Time:</strong> {{ login_time }}</p>
                        <p><strong>IP Address:</strong> {{ ip_address }}</p>
                        <p><strong>Device:</strong> {{ device }}</p>
                        <p><strong>Location:</strong> {{ location }}</p>
                    </div>
                    
                    <p>If this was you, you can ignore this message.</p>
                    
                    <div class="alert">
                        <p><strong>Wasn't you?</strong> If you didn't log in, your account security might be compromised. Please reset your password immediately.</p>
                        <p style="text-align: center;">
                            <a href="{{ site_url }}/accounts/password/reset/" class="button">Reset Password</a>
                        </p>
                    </div>
                    
                    <p>Best regards,<br>The EndevOps Security Team</p>
                </div>
                <div class="footer">
                    <p>© {{ year }} {{ company_name }}. All rights reserved.</p>
                    <p>This email was sent to {{ email }}</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_login_notification_text(self):
        return '''
New Login to Your EndevOps Account

Hello {{ username }},

We detected a new login to your EndevOps account. Here are the details:

Time: {{ login_time }}
IP Address: {{ ip_address }}
Device: {{ device }}
Location: {{ location }}

If this was you, you can ignore this message.

SECURITY ALERT: If you didn't log in, your account security might be compromised. Please reset your password immediately by visiting:
{{ site_url }}/accounts/password/reset/

Best regards,
The EndevOps Security Team

© {{ year }} {{ company_name }}. All rights reserved.
This email was sent to {{ email }}
        '''
    
    def get_password_reset_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reset Your EndevOps Password</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
                .container { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #0061f2 0%, #00c6f9 100%); color: white; padding: 25px; text-align: center; }
                .content { padding: 30px; background-color: white; }
                .button { display: inline-block; background-color: #0061f2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 15px; }
                .button:hover { background-color: #0052cc; }
                .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #f7f9fc; color: #666; font-size: 12px; }
                .note { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0061f2; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reset Your Password</h1>
                </div>
                <div class="content">
                    <p>Hello {{ username }},</p>
                    <p>We received a request to reset your password for your EndevOps account. If you made this request, click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{{ reset_url }}" class="button">Reset Password</a>
                    </p>
                    
                    <div class="note">
                        <p>If the button above doesn't work, you can copy and paste the following link into your browser:</p>
                        <p>{{ reset_url }}</p>
                    </div>
                    
                    <p>This password reset link will expire in 24 hours.</p>
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.</p>
                    
                    <p>Best regards,<br>The EndevOps Team</p>
                </div>
                <div class="footer">
                    <p>© {{ year }} {{ company_name }}. All rights reserved.</p>
                    <p>This email was sent to {{ email }}</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_password_reset_text(self):
        return '''
Reset Your EndevOps Password

Hello {{ username }},

We received a request to reset your password for your EndevOps account. If you made this request, please use the link below to create a new password:

{{ reset_url }}

This password reset link will expire in 24 hours.

If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.

Best regards,
The EndevOps Team

© {{ year }} {{ company_name }}. All rights reserved.
This email was sent to {{ email }}
        ''' 