"""
Management command to send test subscription emails
Usage: python manage.py send_test_subscription_emails nwanzeemmanuelogom@gmail.com
"""
from django.core.management.base import BaseCommand
from customer_subscriptions.email_service import SubscriptionEmailService


class Command(BaseCommand):
    help = 'Send test subscription notification emails'

    def add_arguments(self, parser):
        parser.add_argument('recipient_email', type=str, help='Recipient email address')
        parser.add_argument(
            '--template',
            type=str,
            choices=['skip', 'address', 'renewal', 'cancellation', 'all'],
            default='all',
            help='Which template to test (default: all)'
        )

    def handle(self, *args, **options):
        recipient_email = options['recipient_email']
        template_choice = options['template']
        
        self.stdout.write(self.style.SUCCESS(f'\nSending test emails to: {recipient_email}\n'))
        
        results = []
        
        # Skip notification test
        if template_choice in ['skip', 'all']:
            self.stdout.write('📧 Testing skip notification template...')
            success = SubscriptionEmailService.send_test_email(
                'subscription_skip_notification',
                recipient_email
            )
            results.append(('Skip Notification', success))
            self.stdout.write(
                self.style.SUCCESS('   ✅ Sent!') if success 
                else self.style.ERROR('   ❌ Failed!')
            )
        
        # Address change test
        if template_choice in ['address', 'all']:
            self.stdout.write('📧 Testing address change notification template...')
            success = SubscriptionEmailService.send_test_email(
                'subscription_address_change_notification',
                recipient_email
            )
            results.append(('Address Change', success))
            self.stdout.write(
                self.style.SUCCESS('   ✅ Sent!') if success 
                else self.style.ERROR('   ❌ Failed!')
            )
        
        # Renewal reminder test
        if template_choice in ['renewal', 'all']:
            self.stdout.write('📧 Testing renewal reminder template...')
            success = SubscriptionEmailService.send_test_email(
                'subscription_renewal_reminder',
                recipient_email
            )
            results.append(('Renewal Reminder', success))
            self.stdout.write(
                self.style.SUCCESS('   ✅ Sent!') if success 
                else self.style.ERROR('   ❌ Failed!')
            )
        
        # Cancellation confirmation test
        if template_choice in ['cancellation', 'all']:
            self.stdout.write('📧 Testing cancellation confirmation template...')
            success = SubscriptionEmailService.send_test_email(
                'subscription_cancellation_confirmation',
                recipient_email
            )
            results.append(('Cancellation Confirmation', success))
            self.stdout.write(
                self.style.SUCCESS('   ✅ Sent!') if success 
                else self.style.ERROR('   ❌ Failed!')
            )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        successful = sum(1 for _, success in results if success)
        total = len(results)
        
        if successful == total:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ All {total} test emails sent successfully!\n'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  {successful}/{total} test emails sent successfully\n'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            f'Check {recipient_email} inbox for test emails.\n'
        ))
