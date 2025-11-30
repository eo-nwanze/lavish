from celery import shared_task
from django.utils import timezone
from .models import ScheduledEmail, Newsletter
from .utils import process_scheduled_emails, send_template_email

@shared_task
def process_pending_emails():
    """Process all pending scheduled emails."""
    process_scheduled_emails()

@shared_task
def send_newsletter(newsletter_id):
    """Send a newsletter to all active subscribers."""
    try:
        newsletter = Newsletter.objects.get(id=newsletter_id)
        
        # Get active subscribers
        subscribers = newsletter.subscribers.filter(is_active=True)
        
        # Prepare context
        context = {
            'newsletter': newsletter,
            'unsubscribe_url': f'/unsubscribe/{newsletter.id}/'
        }
        
        # Send to each subscriber
        for subscriber in subscribers:
            context['subscriber'] = subscriber
            send_template_email(
                template_name='newsletter',
                recipient_list=[subscriber.email],
                context=context,
                email_type='newsletter',
                related_object=newsletter
            )
        
        # Update newsletter status
        newsletter.status = 'sent'
        newsletter.sent_at = timezone.now()
        newsletter.save()
        
    except Newsletter.DoesNotExist:
        return False
    except Exception as e:
        if newsletter:
            newsletter.status = 'failed'
            newsletter.save()
        return False
    
    return True

@shared_task
def retry_failed_emails():
    """Retry failed scheduled emails that haven't exceeded max attempts."""
    failed_emails = ScheduledEmail.objects.filter(
        status='failed',
        attempts__lt=3  # Max attempts
    )
    
    for email in failed_emails:
        email.status = 'pending'
        email.save()
        
        # Process the email
        process_scheduled_emails() 