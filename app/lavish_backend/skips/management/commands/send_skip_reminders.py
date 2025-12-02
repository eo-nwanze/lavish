"""
Management command to send skip reminder notifications

Usage:
    python manage.py send_skip_reminders
    python manage.py send_skip_reminders --days-before 7
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from skips.notification_service import SkipNotificationService
from customer_subscriptions.models import CustomerSubscription
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send skip reminder notifications to customers before their order date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=7,
            help='Number of days before order date to send reminder (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS(f'=== Skip Reminder Notification Service ==='))
        self.stdout.write(f'Days before order: {days_before}')
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write('')
        
        # Calculate target date
        target_date = timezone.now().date() + timedelta(days=days_before)
        
        self.stdout.write(f'Looking for subscriptions with next order date: {target_date}')
        
        # Find active subscriptions with orders coming up
        subscriptions = CustomerSubscription.objects.filter(
            status='ACTIVE',
            next_order_date=target_date
        ).select_related('customer')
        
        total_count = subscriptions.count()
        self.stdout.write(f'Found {total_count} subscription(s) to notify')
        self.stdout.write('')
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('No subscriptions found for reminder'))
            return
        
        sent_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            customer_email = subscription.customer.email if hasattr(subscription, 'customer') else subscription.customer_email
            customer_name = "Customer"
            if hasattr(subscription, 'customer') and subscription.customer.first_name:
                customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}".strip()
            
            self.stdout.write(f'Processing: {customer_name} ({customer_email})')
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'  [DRY RUN] Would send reminder to {customer_email}'))
                sent_count += 1
                continue
            
            try:
                success = SkipNotificationService.send_skip_reminder_notification(
                    subscription=subscription,
                    days_until_cutoff=days_before
                )
                
                if success:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Sent reminder to {customer_email}'))
                    sent_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to send to {customer_email}'))
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                logger.error(f'Error sending skip reminder to {customer_email}: {str(e)}')
                failed_count += 1
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Summary ==='))
        self.stdout.write(f'Total subscriptions: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'Sent: {sent_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed_count}'))
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('This was a DRY RUN - no emails were actually sent'))
            self.stdout.write('Remove --dry-run flag to send actual emails')
