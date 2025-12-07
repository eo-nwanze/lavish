"""
Push Django Subscriptions to Shopify
=====================================

Pushes all Django subscriptions that need syncing to Shopify.

Requirements:
- API scopes must be added first (see SHOPIFY_API_SCOPES_REQUIRED.md)
- Customers must exist in Shopify
- Products must exist in Shopify (for line items)

Usage:
    python push_subscriptions_to_shopify.py
    python push_subscriptions_to_shopify.py --dry-run
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customer_subscriptions.models import CustomerSubscription
from customer_subscriptions.bidirectional_sync import subscription_sync
from django.db import transaction


def push_subscriptions(dry_run=False):
    """Push all pending subscriptions to Shopify"""
    
    print("=" * 80)
    print("PUSH SUBSCRIPTIONS TO SHOPIFY")
    print("=" * 80)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No actual changes will be made\n")
    
    # Get subscriptions that need pushing
    subscriptions = CustomerSubscription.objects.filter(
        needs_shopify_push=True
    ).select_related('customer', 'selling_plan')
    
    total = subscriptions.count()
    
    print(f"\n📊 Found {total} subscription(s) needing push\n")
    
    if total == 0:
        print("✅ All subscriptions are already synced!")
        return
    
    results = {
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    for i, subscription in enumerate(subscriptions, 1):
        print(f"\n{i}/{total}. Processing Subscription #{subscription.id}")
        print(f"   {'='*70}")
        print(f"   Customer: {subscription.customer}")
        print(f"   Status: {subscription.status}")
        print(f"   Selling Plan: {subscription.selling_plan.name if subscription.selling_plan else 'None'}")
        print(f"   Next Billing: {subscription.next_billing_date}")
        print(f"   Shopify ID: {subscription.shopify_id or 'Not yet created'}")
        
        # Validation checks
        if not subscription.customer.shopify_id:
            print(f"   ⚠️ SKIPPED: Customer not synced to Shopify")
            results['skipped'] += 1
            continue
        
        if not subscription.line_items:
            print(f"   ⚠️ SKIPPED: No line items")
            results['skipped'] += 1
            continue
        
        if dry_run:
            print(f"   ✅ Would push to Shopify")
            results['successful'] += 1
            continue
        
        # Push to Shopify
        if subscription.shopify_id:
            # Update existing
            print(f"   🔄 Updating existing subscription in Shopify...")
            result = subscription_sync.update_subscription_in_shopify(subscription)
        else:
            # Create new
            print(f"   ➕ Creating new subscription in Shopify...")
            result = subscription_sync.create_subscription_in_shopify(subscription)
        
        if result.get('success'):
            subscription.refresh_from_db()
            print(f"   ✅ SUCCESS")
            print(f"   Shopify ID: {subscription.shopify_id}")
            results['successful'] += 1
        else:
            error_msg = result.get('message', 'Unknown error')
            print(f"   ❌ FAILED: {error_msg}")
            results['failed'] += 1
            results['errors'].append({
                'subscription_id': subscription.id,
                'customer': str(subscription.customer),
                'error': error_msg
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal: {total}")
    print(f"✅ Successful: {results['successful']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⏭️  Skipped: {results['skipped']}")
    
    if results['errors']:
        print(f"\n❌ ERRORS:")
        for error in results['errors']:
            print(f"\n   Subscription #{error['subscription_id']}")
            print(f"   Customer: {error['customer']}")
            print(f"   Error: {error['error']}")
    
    if dry_run:
        print("\n⚠️ This was a dry run - no actual changes were made")
        print("   Run without --dry-run to actually push subscriptions")
    
    print("\n" + "=" * 80)
    
    return results


def check_prerequisites():
    """Check if all prerequisites are met"""
    
    print("\n" + "=" * 80)
    print("CHECKING PREREQUISITES")
    print("=" * 80)
    
    checks = {
        'api_scopes': False,
        'customers': False,
        'selling_plans': False,
        'products': False
    }
    
    # Check API scopes by trying to query subscriptions
    from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
    
    client = EnhancedShopifyAPIClient()
    
    query = """
    query {
      subscriptionContracts(first: 1) {
        edges {
          node {
            id
          }
        }
      }
    }
    """
    
    try:
        result = client.execute_graphql_query(query, {})
        
        if "errors" in result:
            errors = result["errors"]
            for error in errors:
                if error.get('extensions', {}).get('code') == 'ACCESS_DENIED':
                    print("\n❌ API Scopes: Missing")
                    print("   Required scopes:")
                    print("   - read_own_subscription_contracts")
                    print("   - write_own_subscription_contracts")
                    print("\n   See: SHOPIFY_API_SCOPES_REQUIRED.md")
                    checks['api_scopes'] = False
                    break
        else:
            print("\n✅ API Scopes: Ready")
            checks['api_scopes'] = True
    except Exception as e:
        print(f"\n❌ API Scopes: Error - {e}")
    
    # Check customers
    from customers.models import ShopifyCustomer
    
    customers_synced = ShopifyCustomer.objects.filter(shopify_id__isnull=False).count()
    customers_total = ShopifyCustomer.objects.count()
    
    if customers_synced > 0:
        print(f"\n✅ Customers: {customers_synced}/{customers_total} synced to Shopify")
        checks['customers'] = True
    else:
        print(f"\n⚠️ Customers: {customers_synced}/{customers_total} synced")
        checks['customers'] = False
    
    # Check selling plans
    from customer_subscriptions.models import SellingPlan
    
    plans_synced = SellingPlan.objects.filter(shopify_id__isnull=False).count()
    plans_total = SellingPlan.objects.count()
    
    if plans_synced > 0:
        print(f"\n✅ Selling Plans: {plans_synced}/{plans_total} synced to Shopify")
        checks['selling_plans'] = True
    else:
        print(f"\n⚠️ Selling Plans: {plans_synced}/{plans_total} synced")
        checks['selling_plans'] = False
    
    # Check products
    from products.models import ShopifyProduct
    
    products_synced = ShopifyProduct.objects.filter(shopify_id__isnull=False).count()
    products_total = ShopifyProduct.objects.count()
    
    if products_synced > 0:
        print(f"\n✅ Products: {products_synced}/{products_total} synced to Shopify")
        checks['products'] = True
    else:
        print(f"\n⚠️ Products: {products_synced}/{products_total} synced")
        checks['products'] = False
    
    print("\n" + "=" * 80)
    
    all_ready = all(checks.values())
    
    if all_ready:
        print("\n✅ All prerequisites met - Ready to push subscriptions!")
    else:
        print("\n⚠️ Some prerequisites not met - Please fix issues above")
        
        if not checks['api_scopes']:
            print("\n🔴 CRITICAL: API scopes must be added first")
            print("   1. Go to Shopify Partners Dashboard")
            print("   2. Add required scopes (see SHOPIFY_API_SCOPES_REQUIRED.md)")
            print("   3. Reinstall app to your store")
            print("   4. Run this script again")
    
    return all_ready


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PUSH SUBSCRIPTIONS TO SHOPIFY" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Check prerequisites
    ready = check_prerequisites()
    
    if not ready:
        print("\n⚠️ Cannot proceed - fix prerequisites first")
        sys.exit(1)
    
    # Push subscriptions
    results = push_subscriptions(dry_run=dry_run)
    
    # Exit code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

