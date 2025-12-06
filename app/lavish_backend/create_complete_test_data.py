"""
Add orders to test users with correct field names
"""
import django
import os
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customers.models import ShopifyCustomer
from products.models import ShopifyProduct, ShopifyProductVariant
from orders.models import ShopifyOrder, ShopifyOrderLineItem
from decimal import Decimal
from django.utils import timezone

print("\n" + "=" * 80)
print("CREATING ORDERS FOR TEST USERS")
print("=" * 80)

# Get test users
test_user = ShopifyCustomer.objects.get(email="testuser@example.com")
test_user_2 = ShopifyCustomer.objects.get(email="testuser2@example.com")

# Get active products
active_products = ShopifyProduct.objects.filter(status='ACTIVE').first()
if not active_products:
    # Get any product
    active_products = ShopifyProduct.objects.first()

if active_products:
    print(f"📦 Using product: {active_products.title}")
    variant = ShopifyProductVariant.objects.filter(product=active_products).first()
    if variant:
        print(f"   Variant: {variant.title} - ${variant.price}")
else:
    print("❌ No products found")
    exit(1)

# Create orders for test user 1
print(f"\n📝 Creating orders for {test_user.email}...")

# Order 1 - Recent paid order
order_1 = ShopifyOrder.objects.create(
    shopify_id=f"gid://shopify/Order/test_order_1_{int(datetime.now().timestamp())}",
    order_number=f"TEST-{int(datetime.now().timestamp())}-1",
    name=f"#TEST-{int(datetime.now().timestamp())}-1",
    customer=test_user,
    customer_email=test_user.email,
    financial_status="paid",
    fulfillment_status="fulfilled",
    total_price=Decimal("45.90"),
    subtotal_price=Decimal("39.90"),
    total_tax=Decimal("6.00"),
    currency_code="AUD",
    created_at=timezone.now() - timedelta(days=5),
    updated_at=timezone.now() - timedelta(days=5),
    processed_at=timezone.now() - timedelta(days=5)
)

# Add line item to order 1
ShopifyOrderLineItem.objects.create(
    order=order_1,
    shopify_id=f"test_line_item_{order_1.id}_1",
    product=active_products,
    variant=variant,
    title=active_products.title,
    variant_title=variant.title if variant else "Default",
    quantity=1,
    price=variant.price if variant else Decimal("29.99"),
    total_discount=Decimal("0.00")
)

print(f"✅ Created Order 1: {order_1.name} (${order_1.total_price}) - {order_1.financial_status}")

# Order 2 - Pending order
order_2 = ShopifyOrder.objects.create(
    shopify_id=f"gid://shopify/Order/test_order_2_{int(datetime.now().timestamp())}",
    order_number=f"TEST-{int(datetime.now().timestamp())}-2",
    name=f"#TEST-{int(datetime.now().timestamp())}-2",
    customer=test_user,
    customer_email=test_user.email,
    financial_status="pending",
    fulfillment_status="null",  # unfulfilled
    total_price=Decimal("29.99"),
    subtotal_price=Decimal("29.99"),
    total_tax=Decimal("0.00"),
    currency_code="AUD",
    created_at=timezone.now() - timedelta(days=1),
    updated_at=timezone.now() - timedelta(days=1),
    processed_at=timezone.now() - timedelta(days=1)
)

# Add line item to order 2
ShopifyOrderLineItem.objects.create(
    order=order_2,
    shopify_id=f"test_line_item_{order_2.id}_1",
    product=active_products,
    variant=variant,
    title=active_products.title,
    variant_title=variant.title if variant else "Default",
    quantity=1,
    price=variant.price if variant else Decimal("29.99"),
    total_discount=Decimal("0.00")
)

print(f"✅ Created Order 2: {order_2.name} (${order_2.total_price}) - {order_2.financial_status}")

# Create orders for test user 2
print(f"\n📝 Creating orders for {test_user_2.email}...")

# Order 3 - Recent order for test user 2
order_3 = ShopifyOrder.objects.create(
    shopify_id=f"gid://shopify/Order/test_order_3_{int(datetime.now().timestamp())}",
    order_number=f"TEST-{int(datetime.now().timestamp())}-3",
    name=f"#TEST-{int(datetime.now().timestamp())}-3",
    customer=test_user_2,
    customer_email=test_user_2.email,
    financial_status="paid",
    fulfillment_status="null",  # unfulfilled
    total_price=Decimal("59.98"),
    subtotal_price=Decimal("59.98"),
    total_tax=Decimal("0.00"),
    currency_code="AUD",
    created_at=timezone.now() - timedelta(hours=3),
    updated_at=timezone.now() - timedelta(hours=3),
    processed_at=timezone.now() - timedelta(hours=3)
)

# Add line items to order 3 (2 items)
ShopifyOrderLineItem.objects.create(
    order=order_3,
    shopify_id=f"test_line_item_{order_3.id}_1",
    product=active_products,
    variant=variant,
    title=active_products.title,
    variant_title=variant.title if variant else "Default",
    quantity=2,
    price=variant.price if variant else Decimal("29.99"),
    total_discount=Decimal("0.00")
)

print(f"✅ Created Order 3: {order_3.name} (${order_3.total_price}) - {order_3.financial_status}")

# Now test address changes and bidirectional sync
print(f"\n" + "=" * 80)
print("TESTING ADDRESS CHANGES FOR BIDIRECTIONAL SYNC")
print("=" * 80)

# Change address for test user 1
from customers.models import ShopifyCustomerAddress

test_address_1 = ShopifyCustomerAddress.objects.filter(customer=test_user).first()
if test_address_1:
    print(f"📍 Updating address for {test_user.email}...")
    print(f"   Current: {test_address_1.address1}, {test_address_1.city}")
    
    # Update the address
    test_address_1.address1 = "789 Updated Test Street [MODIFIED]"
    test_address_1.address2 = "Suite 42"
    test_address_1.city = "Updated City"
    test_address_1.zip_code = "54321"
    test_address_1.save()
    
    print(f"   Updated: {test_address_1.address1}, {test_address_1.city}")
    print(f"   needs_shopify_push: {getattr(test_address_1, 'needs_shopify_push', 'N/A')}")

# Create new address for test user 2
print(f"\n📍 Creating new address for {test_user_2.email}...")
new_address = ShopifyCustomerAddress.objects.create(
    customer=test_user_2,
    shopify_id=f"temp_address_new_{int(datetime.now().timestamp())}",
    address1="999 Brand New Avenue",
    address2="Floor 3",
    city="Sydney",
    province="New South Wales",
    country="Australia",
    zip_code="2000",
    phone="+61400123456",
    first_name=test_user_2.first_name,
    last_name=test_user_2.last_name,
    is_default=False
)

print(f"✅ Created new address: {new_address.address1}, {new_address.city}")
print(f"   needs_shopify_push: {getattr(new_address, 'needs_shopify_push', 'N/A')}")

# Summary
print(f"\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

for user in [test_user, test_user_2]:
    orders = ShopifyOrder.objects.filter(customer=user).order_by('-created_at')
    addresses = ShopifyCustomerAddress.objects.filter(customer=user)
    
    print(f"\n👤 {user.email} (ID: {user.id}):")
    print(f"   📦 Orders: {orders.count()}")
    for order in orders:
        line_items = ShopifyOrderLineItem.objects.filter(order=order)
        print(f"      {order.name}: ${order.total_price} ({order.financial_status}/{order.fulfillment_status})")
        for item in line_items:
            print(f"        - {item.title} x{item.quantity} @ ${item.price}")
    
    print(f"   📍 Addresses: {addresses.count()}")
    for addr in addresses:
        needs_push = getattr(addr, 'needs_shopify_push', 'N/A')
        print(f"      {addr.address1}, {addr.city} - Push: {needs_push}")

# Check pending sync items
pending_addresses = ShopifyCustomerAddress.objects.filter(needs_shopify_push=True)
print(f"\n🔄 PENDING BIDIRECTIONAL SYNC:")
print(f"   Addresses to push: {pending_addresses.count()}")

for addr in pending_addresses:
    print(f"   📍 {addr.customer.email}: {addr.address1}")

print(f"\n✅ Test setup complete!")
print(f"🚀 Ready to test bidirectional sync with real customer data!")