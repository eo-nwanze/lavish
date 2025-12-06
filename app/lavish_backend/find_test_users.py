"""
Find test users in database
Search for test user with email testuser@example.com and other test users
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customers.models import ShopifyCustomer, ShopifyCustomerAddress
from django.db.models import Q

print("\n" + "=" * 80)
print("SEARCHING FOR TEST USERS IN DATABASE")
print("=" * 80)

# Search for test user with specific email
target_email = "testuser@example.com"
print(f"\n🔍 Looking for test user with email: {target_email}")

target_user = ShopifyCustomer.objects.filter(email=target_email).first()
if target_user:
    print(f"✅ Found target test user:")
    print(f"   ID: {target_user.id}")
    print(f"   Email: {target_user.email}")
    print(f"   Name: {target_user.first_name} {target_user.last_name}")
    print(f"   Shopify ID: {target_user.shopify_id}")
    print(f"   Created: {target_user.created_at}")
else:
    print(f"❌ Test user with email {target_email} not found")

# Search for other test users
print(f"\n🔍 Searching for other test users...")

test_keywords = ['test', 'example', 'demo', 'sample']
test_users = ShopifyCustomer.objects.filter(
    Q(email__icontains='test') |
    Q(email__icontains='example') |
    Q(email__icontains='demo') |
    Q(first_name__icontains='test') |
    Q(last_name__icontains='test')
).order_by('created_at')

if test_users.exists():
    print(f"✅ Found {test_users.count()} test users:")
    for i, user in enumerate(test_users, 1):
        print(f"\n   {i}. ID: {user.id}")
        print(f"      Email: {user.email}")
        print(f"      Name: {user.first_name} {user.last_name}")
        print(f"      Shopify ID: {user.shopify_id}")
        print(f"      Phone: {user.phone or 'N/A'}")
        print(f"      Created: {user.created_at}")
        
        # Check addresses
        addresses = ShopifyCustomerAddress.objects.filter(customer=user)
        if addresses.exists():
            print(f"      Addresses: {addresses.count()}")
            for addr in addresses:
                print(f"        - {addr.address1}, {addr.city}")
                if addr.is_default:
                    print(f"          (Default)")
        else:
            print(f"      Addresses: None")
else:
    print("❌ No test users found")

# Show all customers for reference
print(f"\n📊 Total customers in database: {ShopifyCustomer.objects.count()}")

# Show recent customers (might include test users)
recent_customers = ShopifyCustomer.objects.order_by('-created_at')[:10]
print(f"\n📅 10 Most recent customers:")
for i, customer in enumerate(recent_customers, 1):
    print(f"   {i}. {customer.email} - {customer.first_name} {customer.last_name}")

print("\n" + "=" * 80)