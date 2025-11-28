from django.core.management.base import BaseCommand
from email_manager.models import EmailTemplate, EmailConfiguration
from django.utils import timezone


class Command(BaseCommand):
    help = 'Creates a test email template for the email manager'

    def handle(self, *args, **options):
        # Get default configuration
        config = EmailConfiguration.objects.filter(is_default=True).first()
        
        if not config:
            self.stdout.write(self.style.WARNING('No default email configuration found. Please create one first.'))
            return
            
        # Try to get existing template
        template_name = 'test_email'
        
        if EmailTemplate.objects.filter(name=template_name).exists():
            template = EmailTemplate.objects.get(name=template_name)
            self.stdout.write(self.style.WARNING(f'Updating existing template "{template_name}"...'))
        else:
            template = EmailTemplate(name=template_name)
            self.stdout.write(self.style.SUCCESS(f'Creating new template "{template_name}"...'))
        
        # Update template fields
        template.template_type = 'custom'
        template.subject = 'Test Email from MyComparables'
        template.configuration = config
        template.is_active = True
        
        # HTML content with modern design
        template.html_content = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ subject }}</title>
            <style>
                :root {
                    --primary-color: #611f69;
                    --secondary-color: #7b68ee;
                    --accent-color: #36c5f0;
                    --text-color: #1d1c1d;
                }
                body {
                    font-family: 'Segoe UI', sans-serif;
                    line-height: 1.6;
                    color: var(--text-color);
                    margin: 0;
                    padding: 0;
                }
                #container {
                    max-width: 600px;
                    margin: 0 auto;
                    background: #fff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }
                #header {
                    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                #header h1 {
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }
                #content {
                    padding: 30px;
                }
                #footer {
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border-top: 1px solid #eee;
                }
            </style>
        </head>
        <body>
            <div id="container">
                <div id="header">
                    <h1>{{ subject }}</h1>
                </div>
                <div id="content">
                    <p>Hello {{ recipient_name|default:"there" }},</p>
                    <p>This is a test email from the MyComparables email system. If you're receiving this, the email system is working correctly.</p>
                    <p><strong>Email Details:</strong></p>
                    <ul>
                        <li><strong>Sent at:</strong> {{ timestamp }}</li>
                        <li><strong>Recipient:</strong> {{ recipient_email }}</li>
                        <li><strong>Sender:</strong> {{ sender }}</li>
                    </ul>
                    <p>This email was sent using the {{ config_name }} email configuration.</p>
                    <p>Best regards,<br>The MyComparables Team</p>
                </div>
                <div id="footer">
                    <p>This is an automated test message.</p>
                    <p>&copy; {{ current_year|default:"2024" }} MyComparables. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Plain text content
        template.plain_text_content = '''
        Hello {{ recipient_name|default:"there" }},
        
        This is a test email from the MyComparables email system. If you're receiving this, the email system is working correctly.
        
        Email Details:
        - Sent at: {{ timestamp }}
        - Recipient: {{ recipient_email }}
        - Sender: {{ sender }}
        
        This email was sent using the {{ config_name }} email configuration.
        
        Best regards,
        The MyComparables Team
        
        This is an automated test message.
        © {{ current_year|default:"2024" }} MyComparables. All rights reserved.
        '''
        
        # Variables definition
        template.variables = {
            "recipient_name": "User",
            "recipient_email": "test@example.com",
            "subject": "Test Email from MyComparables",
            "timestamp": str(timezone.now()),
            "sender": config.default_from_email,
            "config_name": config.name,
            "current_year": timezone.now().year
        }
        
        # Save the template
        template.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated test email template "{template_name}"')) 