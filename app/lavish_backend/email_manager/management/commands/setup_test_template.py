from django.core.management.base import BaseCommand
from email_manager.models import EmailTemplate
from django.conf import settings

class Command(BaseCommand):
    help = 'Sets up a test email template for development'

    def handle(self, *args, **options):
        try:
            # Check if test template already exists
            if EmailTemplate.objects.filter(name='Test Template').exists():
                self.stdout.write(self.style.WARNING('Test email template already exists.'))
                return

            # Create test template
            test_template = EmailTemplate.objects.create(
                name='Test Template',
                subject='Test Email from Kora',
                html_content='''
                    <html>
                        <head>
                            <style>
                                body {
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    max-width: 600px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }
                                .header {
                                    background-color: #f8f9fa;
                                    padding: 20px;
                                    text-align: center;
                                    border-radius: 5px;
                                    margin-bottom: 20px;
                                }
                                .content {
                                    background-color: white;
                                    padding: 20px;
                                    border-radius: 5px;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                }
                                .footer {
                                    text-align: center;
                                    margin-top: 20px;
                                    color: #666;
                                    font-size: 0.9em;
                                }
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h1>Welcome to Kora</h1>
                            </div>
                            <div class="content">
                                <p>Hello {{ recipient_name }},</p>
                                <p>This is a test email from the Kora email system. The template is working correctly.</p>
                                <p>You can use this template as a starting point for creating your own email templates.</p>
                                <p>Available variables:</p>
                                <ul>
                                    <li>{{ recipient_name }} - Recipient's name</li>
                                    <li>{{ recipient_email }} - Recipient's email</li>
                                    <li>{{ sender_name }} - Sender's name</li>
                                    <li>{{ sender_email }} - Sender's email</li>
                                    <li>{{ current_date }} - Current date</li>
                                </ul>
                            </div>
                            <div class="footer">
                                <p>This is an automated message from Kora. Please do not reply to this email.</p>
                            </div>
                        </body>
                    </html>
                ''',
                text_content='''
                    Welcome to Kora

                    Hello {{ recipient_name }},

                    This is a test email from the Kora email system. The template is working correctly.

                    You can use this template as a starting point for creating your own email templates.

                    Available variables:
                    - {{ recipient_name }} - Recipient's name
                    - {{ recipient_email }} - Recipient's email
                    - {{ sender_name }} - Sender's name
                    - {{ sender_email }} - Sender's email
                    - {{ current_date }} - Current date

                    This is an automated message from Kora. Please do not reply to this email.
                ''',
                is_active=True,
                description='Test email template for development'
            )

            self.stdout.write(self.style.SUCCESS('Successfully created test email template.'))
            
            # Print template details
            self.stdout.write('\nTest Template Details:')
            self.stdout.write(f'Name: {test_template.name}')
            self.stdout.write(f'Subject: {test_template.subject}')
            self.stdout.write(f'Is Active: {test_template.is_active}')
            self.stdout.write(f'Description: {test_template.description}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test email template: {str(e)}')) 