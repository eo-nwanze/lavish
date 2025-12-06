"""
Push ONLY customer addresses to Shopify
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customers.bidirectional_sync import push_all_pending_addresses
from customers.models import ShopifyCustomerAddress

print("\n" + "=" * 80)
print("PUSH CUSTOMER ADDRESSES TO SHOPIFY")
print("=" * 80)

pending_addresses = ShopifyCustomerAddress.objects.filter(needs_shopify_push=True)
print(f"\n📊 Found {pending_addresses.count()} pending addresses\n")

for addr in pending_addresses:
    print(f"  📍 Customer: {addr.customer.email}")
    print(f"     Address: {addr.address1}")
    if addr.address2:
        print(f"              {addr.address2}")
    print(f"     City: {addr.city}, {addr.province} {addr.zip_code}")
    print(f"     Country: {addr.country}")
    if addr.phone:
        print(f"     Phone: {addr.phone}")
    print(f"     Default: {'Yes' if addr.is_default else 'No'}")
    print(f"     Shopify ID: {addr.shopify_id}")
    is_new = addr.shopify_id.startswith('temp_')
    print(f"     Action: {'CREATE NEW' if is_new else 'UPDATE EXISTING'}")
    print()

if pending_addresses.exists():
    response = input("🚀 Push these addresses to Shopify? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🔄 Pushing addresses to Shopify...")
        result = push_all_pending_addresses()
        
        print(f"\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"  Total: {result['total']}")
        print(f"  ✅ Success: {result['success_count']}")
        print(f"  ❌ Errors: {result['error_count']}")
        
        if result['errors']:
            print(f"\n❌ ERROR DETAILS:")
            for error in result['errors']:
                print(f"\n  Address ID: {error['address_id']}")
                print(f"  Error: {error['error']}")
        
        if result['success_count'] > 0:
            print(f"\n" + "=" * 80)
            print("✅ SUCCESS!")
            print("=" * 80)
            print(f"{result['success_count']} address(es) successfully synced to Shopify!")
            print("\n🔍 Verify in Shopify:")
            print("  1. Go to Shopify Admin → Customers")
            print("  2. Search for: moodreadswithmadi@outlook.com")
            print("  3. Check the customer's addresses")
            print("  4. Look for the updated/new addresses")
            
        print("\n" + "=" * 80)
    else:
        print("\n  ⏭️  Skipped.")
else:
    print("  ✅ No pending addresses to push")

print()
