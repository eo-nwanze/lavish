from django.core.management.base import BaseCommand
from email_manager.models import EmailConfiguration

class Command(BaseCommand):
    help = 'Sets up the email configuration with the provided SMTP settings'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up email configuration...")
        
        # First, remove default flag from any existing configurations
        EmailConfiguration.objects.filter(is_default=True).update(is_default=False)
        
        # Create or update the email configuration
        config, created = EmailConfiguration.objects.update_or_create(
            email_host="server109.web-hosting.com",
            defaults={
                "name": "EndevOps Email",
                "email_host": "server109.web-hosting.com",
                "email_port": 587,
                "email_host_user": "auth@endevops.com",
                "email_host_password": "press30+Five@2025",
                "email_use_tls": True,
                "email_use_ssl": False,
                "default_from_email": "auth@endevops.com",
                "is_default": True,
                "test_email": "test@example.com"  # Add default test email
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS("Email configuration created successfully!"))
        else:
            self.stdout.write(self.style.SUCCESS("Email configuration updated successfully!"))
            
        self.stdout.write(self.style.SUCCESS("Configuration details:"))
        self.stdout.write(f"  Host: {config.email_host}")
        self.stdout.write(f"  Port: {config.email_port}")
        self.stdout.write(f"  User: {config.email_host_user}")
        self.stdout.write(f"  TLS Enabled: {config.email_use_tls}")
        self.stdout.write(f"  Default From: {config.default_from_email}")
        self.stdout.write(f"  Is Default: {config.is_default}")
        self.stdout.write(f"  Test Email: {config.test_email}") 