"""
Management command to bill subscriptions
========================================

This command should be run daily via cron job to automatically
bill all subscriptions that are due.

Usage:
    python manage.py bill_subscriptions
    python manage.py bill_subscriptions --dry-run
    python manage.py bill_subscriptions --retry-failed
    python manage.py bill_subscriptions --bulk
"""

from django.core.management.base import BaseCommand
from customer_subscriptions.tasks import (
    bill_subscriptions_daily,
    retry_failed_subscriptions,
    bulk_bill_subscriptions,
    get_bulk_charge_results
)
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Bill subscriptions due today'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate billing without actually charging customers',
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Retry subscriptions with recent billing failures',
        )
        parser.add_argument(
            '--bulk',
            action='store_true',
            help='Use Shopify bulk billing API (more efficient for large scale)',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for bulk billing (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for bulk billing (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--get-results',
            type=str,
            help='Get results for bulk billing job (provide job ID)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        retry_failed = options['retry_failed']
        use_bulk = options['bulk']
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        job_id = options.get('get_results')
        
        # Get bulk charge results
        if job_id:
            self.stdout.write(self.style.SUCCESS(f"\n📊 Fetching bulk charge results for job: {job_id}\n"))
            results = get_bulk_charge_results(job_id)
            
            if results:
                self.stdout.write(self.style.SUCCESS(f"✅ Retrieved {len(results)} results"))
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to get results"))
            return
        
        # Retry failed billings
        if retry_failed:
            self.stdout.write(self.style.SUCCESS("\n🔄 Retrying failed billing attempts...\n"))
            results = retry_failed_subscriptions()
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Retry complete:"))
            self.stdout.write(f"   Total: {results['total']}")
            self.stdout.write(f"   Successful: {results['successful']}")
            self.stdout.write(f"   Failed: {results['failed']}")
            return
        
        # Bulk billing
        if use_bulk:
            if not start_date:
                start_date = date.today().isoformat() + "T00:00:00Z"
            if not end_date:
                end_date = (date.today() + timedelta(days=1)).isoformat() + "T00:00:00Z"
            
            self.stdout.write(self.style.SUCCESS(f"\n📊 Using bulk billing API\n"))
            self.stdout.write(f"   Date range: {start_date} to {end_date}")
            
            result = bulk_bill_subscriptions(start_date, end_date)
            
            if result:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Bulk charge job created:"))
                self.stdout.write(f"   Job ID: {result['job_id']}")
                self.stdout.write(f"\n   Check results in 1-2 minutes with:")
                self.stdout.write(f"   python manage.py bill_subscriptions --get-results {result['job_id']}")
            else:
                self.stdout.write(self.style.ERROR("\n❌ Bulk charge failed"))
            return
        
        # Regular billing (default)
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN MODE - No actual charges will be made\n"))
        else:
            self.stdout.write(self.style.SUCCESS("\n💳 BILLING SUBSCRIPTIONS DUE TODAY\n"))
        
        results = bill_subscriptions_daily(dry_run=dry_run)
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS("BILLING RESULTS"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))
        
        self.stdout.write(f"Total due: {results['total']}")
        self.stdout.write(self.style.SUCCESS(f"✅ Successful: {results['successful']}"))
        self.stdout.write(self.style.ERROR(f"❌ Failed: {results['failed']}"))
        self.stdout.write(self.style.WARNING(f"⏭️  Skipped: {results['skipped']}"))
        
        if results['errors']:
            self.stdout.write(self.style.ERROR(f"\n❌ Errors:"))
            for error in results['errors'][:10]:  # Show first 10
                self.stdout.write(f"   - Subscription {error.get('subscription_id')}: {error.get('error')}")
        
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nNote: This was a dry run. No charges were made."))
            self.stdout.write("Run without --dry-run to actually bill customers.")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Billing complete!"))

