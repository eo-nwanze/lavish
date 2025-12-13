"""
Quick Resync Script - Push All Selling Plans to Shopify

This script will:
1. Load all selling plans from Django
2. Push each one to Shopify with correct discount percentages
3. Show results for each plan
"""

from customer_subscriptions.models import SellingPlan
from customer_subscriptions.bidirectional_sync import SubscriptionBidirectionalSync
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def resync_all_selling_plans():
    """Resync all selling plans to Shopify"""
    print("\n" + "="*80)
    print("SELLING PLAN RESYNC TO SHOPIFY")
    print("="*80 + "\n")
    
    sync = SubscriptionBidirectionalSync()
    plans = SellingPlan.objects.all().order_by('id')
    
    print(f"Found {plans.count()} selling plans to sync\n")
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    for plan in plans:
        print(f"\n{'─'*80}")
        print(f"📤 Pushing: {plan.name}")
        print(f"   Django has: {plan.price_adjustment_value}% discount")
        print(f"   Type: {plan.price_adjustment_type}")
        print(f"   Interval: {plan.billing_interval_count} {plan.billing_interval}")
        
        try:
            result = sync.create_selling_plan_in_shopify(plan)
            
            if result.get('success'):
                results["success"] += 1
                print(f"   ✅ SUCCESS: {result.get('message')}")
                print(f"   Shopify ID: {result.get('shopify_id')}")
            else:
                results["failed"] += 1
                error_msg = result.get('message', 'Unknown error')
                results["errors"].append(f"{plan.name}: {error_msg}")
                print(f"   ❌ FAILED: {error_msg}")
                
        except Exception as e:
            results["failed"] += 1
            error_msg = str(e)
            results["errors"].append(f"{plan.name}: {error_msg}")
            print(f"   ❌ EXCEPTION: {error_msg}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SYNC SUMMARY")
    print("="*80)
    print(f"✅ Successful: {results['success']}/{plans.count()}")
    print(f"❌ Failed: {results['failed']}/{plans.count()}")
    
    if results["errors"]:
        print(f"\n⚠️  ERRORS:")
        for error in results["errors"]:
            print(f"   - {error}")
    
    print("\n" + "="*80)
    
    if results["success"] == plans.count():
        print("✅ ALL PLANS SYNCED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Refresh your Shopify product page")
        print("2. Check browser console for updated percentages")
        print("3. Verify discounts show correctly on frontend")
    elif results["success"] > 0:
        print("⚠️  PARTIAL SUCCESS")
        print(f"\n{results['success']} plans synced, but {results['failed']} failed.")
        print("Check errors above and try again for failed plans.")
    else:
        print("❌ ALL SYNCS FAILED")
        print("\nPossible issues:")
        print("- Shopify API credentials not configured")
        print("- Network connection issues")
        print("- Shopify API format changed")
        print("- Check Django logs for more details")
    
    print("="*80 + "\n")
    
    return results

if __name__ == "__main__":
    resync_all_selling_plans()

