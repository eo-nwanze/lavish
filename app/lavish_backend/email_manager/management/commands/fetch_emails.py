"""
Management command to fetch emails from all configured inboxes
"""
from django.core.management.base import BaseCommand
from email_manager.inbox_service import fetch_all_inboxes
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch emails from all configured inboxes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inbox-id',
            type=int,
            help='Fetch emails from a specific inbox ID',
        )

    def handle(self, *args, **options):
        inbox_id = options.get('inbox_id')
        
        if inbox_id:
            # Fetch emails from a specific inbox
            from email_manager.models import EmailInbox
            from email_manager.inbox_service import EmailFetchService
            
            try:
                inbox = EmailInbox.objects.get(pk=inbox_id, is_active=True)
                
                if not inbox.incoming_config:
                    self.stdout.write(self.style.ERROR(f'Inbox {inbox_id} has no incoming mail configuration'))
                    return
                
                if not inbox.incoming_config.is_active:
                    self.stdout.write(self.style.ERROR(f'Inbox {inbox_id} incoming mail configuration is inactive'))
                    return
                
                service = EmailFetchService(inbox.incoming_config)
                count = service.fetch_emails(inbox)
                
                self.stdout.write(self.style.SUCCESS(f'Successfully fetched {count} email(s) from inbox {inbox.name}'))
                
            except EmailInbox.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Inbox with ID {inbox_id} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error fetching emails: {str(e)}'))
                logger.error(f'Error fetching emails for inbox {inbox_id}: {str(e)}')
        else:
            # Fetch emails from all inboxes
            self.stdout.write('Fetching emails from all configured inboxes...')
            
            results = fetch_all_inboxes()
            
            total_success = 0
            total_errors = 0
            
            for email_address, result in results.items():
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(
                        f'{email_address}: Fetched {result["count"]} email(s)'
                    ))
                    total_success += result['count']
                else:
                    self.stdout.write(self.style.ERROR(
                        f'{email_address}: {result["error"]}'
                    ))
                    total_errors += 1
            
            if total_success > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'\nTotal: Fetched {total_success} email(s) from {len(results) - total_errors} inbox(es)'
                ))
            
            if total_errors > 0:
                self.stdout.write(self.style.WARNING(
                    f'{total_errors} inbox(es) had errors'
                ))
