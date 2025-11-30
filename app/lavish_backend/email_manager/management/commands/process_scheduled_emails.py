from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template import Template, Context
from django.template.loader import render_to_string
import logging
from kora.models import ScheduledEmail, EmailHistory
from kora.utils import send_and_log_email
import traceback

class Command(BaseCommand):
    help = 'Process scheduled emails that are due to be sent'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Run in debug mode (does not actually send emails)',
        )
    
    def handle(self, *args, **options):
        debug_mode = options.get('debug', False)
        logger = logging.getLogger(__name__)
        
        now = timezone.now()
        self.stdout.write(f"Processing scheduled emails due by {now}")
        
        # Get all pending emails scheduled to be sent before or at the current time
        scheduled_emails = ScheduledEmail.objects.filter(
            status='pending',
            scheduled_time__lte=now
        ).order_by('scheduled_time')
        
        if not scheduled_emails:
            self.stdout.write("No scheduled emails to process")
            return
        
        self.stdout.write(f"Found {scheduled_emails.count()} scheduled emails to process")
        
        for email in scheduled_emails:
            self.stdout.write(f"Processing email: {email}")
            
            # Mark as in progress to avoid duplicate processing
            email.status = 'sending'
            email.attempts += 1
            email.last_attempt = now
            email.save()
            
            try:
                if debug_mode:
                    self.stdout.write(f"[DEBUG] Would send to {len(email.recipients)} recipients: {email.recipients}")
                    email.status = 'pending'  # Reset to pending in debug mode
                    email.save()
                    continue
                
                # Get template content
                subject = email.subject_override or email.template.subject
                html_content = email.template.html_content
                plain_text_content = email.template.plain_text_content
                
                # Process variables
                variables = email.variables_data or {}
                
                # Ensure current_year is available
                if 'current_year' not in variables:
                    variables['current_year'] = timezone.now().year
                
                # Add unsubscribe URL for each recipient (if not already added in variables)
                if 'unsubscribe_url' not in variables:
                    from django.conf import settings
                    site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
                    variables['unsubscribe_url'] = f"{site_url}/newsletter/unsubscribe/"
                
                # Process the template context
                context = Context(variables)
                template_subject = Template(subject)
                template_html = Template(html_content)
                template_plain = Template(plain_text_content)
                
                rendered_subject = template_subject.render(context)
                rendered_html = template_html.render(context)
                rendered_plain = template_plain.render(context)
                
                # Send to all recipients
                successful_sends = 0
                failed_sends = 0
                
                for recipient in email.recipients:
                    try:
                        success = send_and_log_email(
                            subject=rendered_subject,
                            message=rendered_plain,
                            html_message=rendered_html,
                            recipient_email=recipient,
                            email_type='scheduled_email',
                            content_object=email
                        )
                        
                        if success:
                            successful_sends += 1
                        else:
                            failed_sends += 1
                            logger.error(f"Failed to send email to {recipient}")
                            
                    except Exception as e:
                        failed_sends += 1
                        logger.error(f"Error sending to {recipient}: {str(e)}")
                        logger.error(traceback.format_exc())
                
                # Update email status
                email.status = 'sent'
                email.sent_time = timezone.now()
                email.save()
                
                # Update related newsletter if this is part of a newsletter
                if 'newsletter_id' in variables:
                    try:
                        from kora.models import Newsletter
                        newsletter = Newsletter.objects.get(id=variables['newsletter_id'])
                        newsletter.successful_sends = successful_sends
                        newsletter.failed_sends = failed_sends
                        newsletter.total_recipients = len(email.recipients)
                        newsletter.sent_time = timezone.now()
                        newsletter.status = 'sent'
                        newsletter.save()
                    except Exception as e:
                        logger.error(f"Error updating newsletter: {str(e)}")
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully processed scheduled email: {successful_sends} sent, {failed_sends} failed"
                ))
                
            except Exception as e:
                logger.error(f"Error processing scheduled email {email.id}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Update status to failed
                email.status = 'failed'
                email.error_message = str(e)
                email.save()
                
                self.stdout.write(self.style.ERROR(f"Failed to process scheduled email: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS("Finished processing scheduled emails")) 