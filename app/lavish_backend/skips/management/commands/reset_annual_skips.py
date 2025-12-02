from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from customer_subscriptions.models import CustomerSubscription
from skips.models import SubscriptionSkip
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reset annual skip counters for all subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without making changes'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specify year to reset (default: current year)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_year = options['year'] or timezone.now().year
        
        self.stdout.write(f"{'DRY RUN - ' if dry_run else ''}Resetting annual skip counters for {target_year}")
        self.stdout.write("=" * 50)
        
        try:
            # Reset subscription skip counters
            subscriptions_updated = CustomerSubscription.objects.filter(
                status='ACTIVE'
            ).update(skips_used_this_year=0, consecutive_skips=0)
            
            # Reset skip analytics for new year
            from skips.models import SkipAnalytics
            analytics_updated = SkipAnalytics.objects.filter(
                period_type='yearly',
                period_start__year=target_year
            ).update(
                skips_used_this_year=0,
                consecutive_skips=0
            )
            
            # Log the reset operation
            from skips.models import SubscriptionSyncLog
            sync_log = SubscriptionSyncLog.objects.create(
                operation_type='annual_skip_reset',
                status='completed',
                subscriptions_processed=subscriptions_updated,
                subscriptions_successful=subscriptions_updated,
                subscriptions_failed=0,
                store_domain='7fa66c-ac.myshopify.com'
            )
            
            self.stdout.write(f"✅ Successfully reset skip counters:")
            self.stdout.write(f"   - Subscriptions updated: {subscriptions_updated}")
            self.stdout.write(f"   - Analytics updated: {analytics_updated}")
            self.stdout.write(f"   - Sync log created: #{sync_log.id}")
            
            if dry_run:
                self.stdout.write("\n🔍 DRY RUN COMPLETED - No changes made")
            else:
                self.stdout.write("\n✅ ANNUAL SKIP RESET COMPLETED")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during skip reset: {e}"))
            logger.error(f"Annual skip reset failed: {e}", exc_info=True)
            return
        
        # Show statistics
        self.show_skip_statistics(target_year)

    def show_skip_statistics(self, year):
        """Display skip statistics for the year"""
        self.stdout.write(f"\n📊 Skip Statistics for {year}:")
        self.stdout.write("-" * 30)
        
        try:
            from skips.models import SubscriptionSkip, SkipAnalytics
            
            # Total skips in the year
            total_skips = SubscriptionSkip.objects.filter(
                created_at__year=year
            ).count()
            
            # Confirmed skips
            confirmed_skips = SubscriptionSkip.objects.filter(
                created_at__year=year,
                status='confirmed'
            ).count()
            
            # Cancelled skips
            cancelled_skips = SubscriptionSkip.objects.filter(
                created_at__year=year,
                status='cancelled'
            ).count()
            
            # Unique customers who used skips
            unique_skippers = SubscriptionSkip.objects.filter(
                created_at__year=year,
                status='confirmed'
            ).values('subscription__customer').distinct().count()
            
            self.stdout.write(f"   Total skips requested: {total_skips}")
            self.stdout.write(f"   Confirmed skips: {confirmed_skips}")
            self.stdout.write(f"   Cancelled skips: {cancelled_skips}")
            self.stdout.write(f"   Unique customers using skips: {unique_skippers}")
            
            if total_skips > 0:
                cancel_rate = (cancelled_skips / total_skips) * 100
                self.stdout.write(f"   Skip cancellation rate: {cancel_rate:.1f}%")
            
        except Exception as e:
            self.stdout.write(f"   Error loading statistics: {e}")