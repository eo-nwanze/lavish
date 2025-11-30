from django.core.management.base import BaseCommand
from email_manager.models import EmailConfiguration, EmailTemplate
from django.core.mail import send_mail
from django.conf import settings
from django.template import Context, Template
from datetime import datetime

class Command(BaseCommand):
    help = 'Tests the email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('--recipient', type=str, help='Recipient email address')
        parser.add_argument('--recipient-name', type=str, help='Recipient name')

    def handle(self, *args, **options):
        try:
            # Get the default email configuration
            config = EmailConfiguration.objects.filter(is_default=True).first()
            if not config:
                self.stdout.write(self.style.ERROR('No default email configuration found.'))
                return

            # Get the test template
            template = EmailTemplate.objects.filter(name='Test Template').first()
            if not template:
                self.stdout.write(self.style.ERROR('Test template not found. Please run setup_test_template first.'))
                return

            # Get recipient details
            recipient_email = options.get('recipient') or 'test@example.com'
            recipient_name = options.get('recipient_name') or 'Test User'

            # Prepare context for template
            context = {
                'recipient_name': recipient_name,
                'recipient_email': recipient_email,
                'sender_name': 'Kora Admin',
                'sender_email': config.email_host_user,
                'current_date': datetime.now().strftime('%Y-%m-%d')
            }

            # Render templates
            html_content = Template(template.html_content).render(Context(context))
            text_content = Template(template.text_content).render(Context(context))

            # Send test email
            send_mail(
                subject=template.subject,
                message=text_content,
                from_email=config.email_host_user,
                recipient_list=[recipient_email],
                html_message=html_content,
                fail_silently=False,
                auth_user=config.email_host_user,
                auth_password=config.email_host_password,
                connection=None,
                use_tls=config.email_use_tls,
                use_ssl=config.email_use_ssl,
                timeout=config.email_timeout
            )

            self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to {recipient_email}'))
            self.stdout.write(self.style.SUCCESS('Please check your inbox for the test email.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending test email: {str(e)}'))
            self.stdout.write(self.style.ERROR('Please check your email configuration and try again.')) 