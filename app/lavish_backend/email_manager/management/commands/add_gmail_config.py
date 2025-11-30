from django.core.management.base import BaseCommand
from kora.models import EmailConfiguration

class Command(BaseCommand):
    help = 'Add Gmail email configuration to the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Gmail email address',
            default=None,
            required=True
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Gmail app password (create one at https://myaccount.google.com/apppasswords)',
            default=None,
            required=True
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Configuration name',
            default='Gmail'
        )
        parser.add_argument(
            '--default',
            action='store_true',
            help='Set as default configuration',
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        name = options['name']
        is_default = options['default']
        
        # Check if configuration with this name already exists
        existing = EmailConfiguration.objects.filter(name=name).first()
        if existing:
            self.stdout.write(self.style.WARNING(f"Configuration with name '{name}' already exists. Updating it..."))
            config = existing
        else:
            config = EmailConfiguration(name=name)
        
        # Set Gmail SMTP settings
        config.email_host = 'smtp.gmail.com'
        config.email_port = 587
        config.email_host_user = email
        config.email_host_password = password
        config.email_use_tls = True
        config.email_use_ssl = False
        config.default_from_email = email
        config.is_default = is_default
        
        # If this is set as default, unset other defaults
        if is_default:
            EmailConfiguration.objects.filter(is_default=True).exclude(id=config.id if config.id else 0).update(is_default=False)
        
        config.save()
        
        self.stdout.write(self.style.SUCCESS(f"Successfully {'updated' if existing else 'added'} Gmail configuration '{name}'"))
        if is_default:
            self.stdout.write(self.style.SUCCESS("Set as default email configuration"))
        
        self.stdout.write("\nYou can now use this configuration to send emails!")
        self.stdout.write("Important: Make sure you've created an App Password for your Gmail account at https://myaccount.google.com/apppasswords")
        self.stdout.write("Regular passwords won't work with Gmail SMTP due to security restrictions.") 