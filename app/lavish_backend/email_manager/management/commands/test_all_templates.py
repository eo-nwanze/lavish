from django.core.management.base import BaseCommand
from django.template import Template, Context
from email_manager.models import EmailTemplate, EmailConfiguration
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Command(BaseCommand):
    help = 'Send test emails for all subscription templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='nwanzeemmanuelogom@gmail.com',
            help='Email address to send test emails to'
        )

    def handle(self, *args, **options):
        recipient_email = options['email']
        self.stdout.write(f'Sending test emails to {recipient_email}...\n')
        
        # Get default configuration
        config = EmailConfiguration.objects.filter(is_default=True).first()
        
        if not config:
            self.stdout.write(self.style.ERROR('No default email configuration found'))
            return
        
        # List of all subscription templates
        template_names = [
            'subscription_welcome',
            'subscription_payment_failure',
            'subscription_address_reminder',
            'subscription_renewal_notice',
            'subscription_skip_notification',
            'subscription_address_change_notification',
            'subscription_renewal_reminder',
            'subscription_cancellation_confirmation',
        ]
        
        sent_count = 0
        failed_count = 0
        
        for template_name in template_names:
            try:
                template = EmailTemplate.objects.get(name=template_name)
                
                # Render subject
                subject_template = Template(template.subject)
                subject = subject_template.render(Context(template.variables))
                
                # Render HTML content
                html_template = Template(template.html_content)
                html_content = html_template.render(Context(template.variables))
                
                # Render plain text content
                text_template = Template(template.plain_text_content)
                text_content = text_template.render(Context(template.variables))
                
                # Send email using smtplib
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # Connect to SMTP server
                if config.email_use_ssl:
                    server = smtplib.SMTP_SSL(config.email_host, config.email_port, context=context)
                else:
                    server = smtplib.SMTP(config.email_host, config.email_port)
                    if config.email_use_tls:
                        server.starttls(context=context)
                
                # Login
                if config.email_host_user and config.email_host_password:
                    server.login(config.email_host_user, config.email_host_password)
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = config.default_from_email
                msg['To'] = recipient_email
                
                part1 = MIMEText(text_content, 'plain')
                part2 = MIMEText(html_content, 'html')
                
                msg.attach(part1)
                msg.attach(part2)
                
                # Send
                server.send_message(msg)
                server.quit()
                
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Sent: {template_name}'))
                    
            except EmailTemplate.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠️  Template not found: {template_name}'))
                failed_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error with {template_name}: {str(e)}'))
                failed_count += 1
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Sent: {sent_count} emails'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {failed_count} emails'))
        self.stdout.write(f'\n📧 All test emails sent to: {recipient_email}\n')
