"""
LIVE TEST: Push to Shopify
Tests pushing inventory and address changes to Shopify
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.bidirectional_sync import push_all_pending_inventory
from customers.bidirectional_sync import push_all_pending_addresses
from inventory.models import ShopifyInventoryLevel
from customers.models import ShopifyCustomerAddress

print("\n" + "=" * 80)
print("LIVE PUSH TO SHOPIFY TEST")
print("=" * 80)

# ======================== PUSH ADDRESSES ========================
print("\n" + "=" * 80)
print("1. PUSHING CUSTOMER ADDRESSES TO SHOPIFY")
print("=" * 80)

pending_addresses = ShopifyCustomerAddress.objects.filter(needs_shopify_push=True)
print(f"\n📊 Found {pending_addresses.count()} pending addresses")

if pending_addresses.exists():
    print("\n  Details:")
    for addr in pending_addresses:
        print(f"    • Customer: {addr.customer.email}")
        print(f"      Address: {addr.address1}, {addr.city}")
        print(f"      Customer Shopify ID: {addr.customer.shopify_id}")
        print(f"      Address Shopify ID: {addr.shopify_id}")
    
    response = input("\n🚀 Push these addresses to Shopify? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🔄 Pushing addresses...")
        result = push_all_pending_addresses()
        
        print(f"\n✅ RESULTS:")
        print(f"  Total: {result['total']}")
        print(f"  Success: {result['success_count']}")
        print(f"  Errors: {result['error_count']}")
        
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"  • Address {error['address_id']}: {error['error']}")
        
        if result['success_count'] > 0:
            print(f"\n✅ {result['success_count']} address(es) successfully pushed to Shopify!")
            print(f"   Check Shopify Admin → Customers to verify")
    else:
        print("  Skipped.")
else:
    print("  ✅ No pending addresses to push")

# ======================== PUSH INVENTORY ========================
print("\n" + "=" * 80)
print("2. PUSHING INVENTORY LEVELS TO SHOPIFY")
print("=" * 80)

pending_inventory = ShopifyInventoryLevel.objects.filter(needs_shopify_push=True)
print(f"\n📊 Found {pending_inventory.count()} pending inventory levels")

if pending_inventory.exists():
    print("\n  Details:")
    for level in pending_inventory:
        print(f"    • SKU: {level.inventory_item.sku}")
        print(f"      Location: {level.location.name}")
        print(f"      Available: {level.available}")
        print(f"      Inventory Item ID: {level.inventory_item.shopify_id}")
        print(f"      Location ID: {level.location.shopify_id}")
    
    # Check if IDs are valid (not test/temp IDs)
    has_invalid_ids = False
    for level in pending_inventory:
        if (level.inventory_item.shopify_id.startswith('test_') or 
            level.location.shopify_id.startswith('test_')):
            has_invalid_ids = True
            break
    
    if has_invalid_ids:
        print("\n⚠️  WARNING: Some inventory items have test/temp Shopify IDs")
        print("   These need real Shopify IDs before they can be pushed")
        print("   Recommendation: Sync products from Shopify first")
    else:
        response = input("\n🚀 Push these inventory levels to Shopify? (yes/no): ")
        
        if response.lower() == 'yes':
            print("\n🔄 Pushing inventory...")
            result = push_all_pending_inventory()
            
            print(f"\n✅ RESULTS:")
            print(f"  Total: {result['total']}")
            print(f"  Success: {result['success_count']}")
            print(f"  Errors: {result['error_count']}")
            
            if result['errors']:
                print(f"\n❌ Errors:")
                for error in result['errors']:
                    print(f"  • {error['sku']} at {error['location']}: {error['error']}")
            
            if result['success_count'] > 0:
                print(f"\n✅ {result['success_count']} inventory level(s) successfully pushed to Shopify!")
                print(f"   Check Shopify Admin → Products → Inventory to verify")
        else:
            print("  Skipped.")
else:
    print("  ✅ No pending inventory to push")

# ======================== VERIFICATION ========================
print("\n" + "=" * 80)
print("3. VERIFICATION STEPS")
print("=" * 80)

print("""
🔍 To verify the changes in Shopify:

Customer Addresses:
-------------------
1. Go to Shopify Admin → Customers
2. Search for the customer email
3. Check their addresses
4. Verify the updated/new addresses appear

Inventory Levels:
-----------------
1. Go to Shopify Admin → Products
2. Click on the product
3. Click "Inventory" tab
4. Check the quantity at each location
5. Verify the updated quantities match Django

📊 Real-time Sync Status:
------------------------
- Changes made in Django are now AUTO-FLAGGED for Shopify push
- Run push functions periodically or set up a cron job
- Webhook updates from Shopify still update Django (one-way remains)
- You now have true bidirectional sync! 🎉
""")

print("=" * 80)
