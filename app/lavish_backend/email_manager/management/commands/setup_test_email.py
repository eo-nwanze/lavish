from django.core.management.base import BaseCommand
from email_manager.models import EmailConfiguration
from django.conf import settings

class Command(BaseCommand):
    help = 'Sets up a test email configuration for development'

    def handle(self, *args, **options):
        try:
            # Check if test configuration already exists
            if EmailConfiguration.objects.filter(name='Test Configuration').exists():
                self.stdout.write(self.style.WARNING('Test email configuration already exists.'))
                return

            # Create test configuration
            test_config = EmailConfiguration.objects.create(
                name='Test Configuration',
                email_host='smtp.gmail.com',
                email_port=587,
                email_host_user='test@example.com',
                email_host_password='your-test-password',
                email_use_tls=True,
                email_use_ssl=False,
                email_timeout=30,
                is_default=True,
                description='Test email configuration for development'
            )

            self.stdout.write(self.style.SUCCESS('Successfully created test email configuration.'))
            self.stdout.write(self.style.SUCCESS('Please update the email credentials in the admin panel.'))
            
            # Print configuration details
            self.stdout.write('\nTest Configuration Details:')
            self.stdout.write(f'Name: {test_config.name}')
            self.stdout.write(f'Host: {test_config.email_host}')
            self.stdout.write(f'Port: {test_config.email_port}')
            self.stdout.write(f'Username: {test_config.email_host_user}')
            self.stdout.write(f'Use TLS: {test_config.email_use_tls}')
            self.stdout.write(f'Use SSL: {test_config.email_use_ssl}')
            self.stdout.write(f'Timeout: {test_config.email_timeout} seconds')
            self.stdout.write(f'Is Default: {test_config.is_default}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test email configuration: {str(e)}')) 