"""
Django Management Command: Resync Selling Plans to Shopify
"""

from django.core.management.base import BaseCommand
from customer_subscriptions.models import SellingPlan
from customer_subscriptions.bidirectional_sync import SubscriptionBidirectionalSync
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Resync all selling plans to Shopify with correct discount percentages'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("SELLING PLAN RESYNC TO SHOPIFY"))
        self.stdout.write("="*80 + "\n")
        
        sync = SubscriptionBidirectionalSync()
        plans = SellingPlan.objects.all().order_by('id')
        
        self.stdout.write(f"Found {plans.count()} selling plans to sync\n")
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for plan in plans:
            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write(f"Pushing: {plan.name}")
            self.stdout.write(f"   Django has: {plan.price_adjustment_value}% discount")
            self.stdout.write(f"   Type: {plan.price_adjustment_type}")
            self.stdout.write(f"   Interval: {plan.billing_interval_count} {plan.billing_interval}")
            
            try:
                result = sync.create_selling_plan_in_shopify(plan)
                
                if result.get('success'):
                    results["success"] += 1
                    self.stdout.write(self.style.SUCCESS(f"   SUCCESS: {result.get('message')}"))
                    self.stdout.write(f"   Shopify ID: {result.get('shopify_id')}")
                else:
                    results["failed"] += 1
                    error_msg = result.get('message', 'Unknown error')
                    results["errors"].append(f"{plan.name}: {error_msg}")
                    self.stdout.write(self.style.ERROR(f"   FAILED: {error_msg}"))
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = str(e)
                results["errors"].append(f"{plan.name}: {error_msg}")
                self.stdout.write(self.style.ERROR(f"   EXCEPTION: {error_msg}"))
        
        # Summary
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS("SYNC SUMMARY"))
        self.stdout.write("="*80)
        self.stdout.write(f"Successful: {results['success']}/{plans.count()}")
        self.stdout.write(f"Failed: {results['failed']}/{plans.count()}")
        
        if results["errors"]:
            self.stdout.write(self.style.WARNING(f"\nERRORS:"))
            for error in results["errors"]:
                self.stdout.write(f"   - {error}")
        
        self.stdout.write("\n" + "="*80)
        
        if results["success"] == plans.count():
            self.stdout.write(self.style.SUCCESS("ALL PLANS SYNCED SUCCESSFULLY!"))
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Refresh your Shopify product page")
            self.stdout.write("2. Check browser console for updated percentages")
            self.stdout.write("3. Verify discounts show correctly on frontend")
        elif results["success"] > 0:
            self.stdout.write(self.style.WARNING("PARTIAL SUCCESS"))
            self.stdout.write(f"\n{results['success']} plans synced, but {results['failed']} failed.")
            self.stdout.write("Check errors above and try again for failed plans.")
        else:
            self.stdout.write(self.style.ERROR("ALL SYNCS FAILED"))
            self.stdout.write("\nPossible issues:")
            self.stdout.write("- Shopify API credentials not configured")
            self.stdout.write("- Network connection issues")
            self.stdout.write("- Shopify API format changed")
            self.stdout.write("- Check Django logs for more details")
        
        self.stdout.write("="*80 + "\n")

