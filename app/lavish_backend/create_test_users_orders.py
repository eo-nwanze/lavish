"""
Create test users and add orders for bidirectional sync testing
Focus on testuser@example.com and create Test User 2
"""
import django
import os
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customers.models import ShopifyCustomer, ShopifyCustomerAddress
from products.models import ShopifyProduct
from orders.models import ShopifyOrder, ShopifyOrderLineItem
from decimal import Decimal

print("\n" + "=" * 80)
print("CREATING TEST USERS AND ORDERS")
print("=" * 80)

# Create testuser@example.com if not exists
target_email = "testuser@example.com"
test_user = ShopifyCustomer.objects.filter(email=target_email).first()

if not test_user:
    print(f"\n📝 Creating test user: {target_email}")
    test_user = ShopifyCustomer.objects.create(
        email=target_email,
        first_name="Test",
        last_name="User",
        shopify_id=f"gid://shopify/Customer/test_{int(datetime.now().timestamp())}",
        phone="+1234567890",
        accepts_marketing=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    print(f"✅ Created test user with ID: {test_user.id}")
else:
    print(f"✅ Test user {target_email} already exists (ID: {test_user.id})")

# Create address for test user
test_address = ShopifyCustomerAddress.objects.filter(customer=test_user).first()
if not test_address:
    print(f"📝 Creating address for test user...")
    test_address = ShopifyCustomerAddress.objects.create(
        customer=test_user,
        shopify_id=f"temp_address_test_{int(datetime.now().timestamp())}",
        address1="123 Test Street",
        address2="Apt 4B",
        city="Test City",
        province="Test State",
        country="Australia",
        zip_code="12345",
        phone="+1234567890",
        first_name="Test",
        last_name="User",
        is_default=True
    )
    print(f"✅ Created address with ID: {test_address.id}")
else:
    print(f"✅ Test user already has address: {test_address.address1}")

# Create Test User 2
test_user_2_email = "testuser2@example.com"
test_user_2 = ShopifyCustomer.objects.filter(email=test_user_2_email).first()

if not test_user_2:
    print(f"\n📝 Creating Test User 2: {test_user_2_email}")
    test_user_2 = ShopifyCustomer.objects.create(
        email=test_user_2_email,
        first_name="Test",
        last_name="User Two",
        shopify_id=f"gid://shopify/Customer/test2_{int(datetime.now().timestamp())}",
        phone="+0987654321",
        accepts_marketing=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    print(f"✅ Created Test User 2 with ID: {test_user_2.id}")
    
    # Create address for Test User 2
    test_address_2 = ShopifyCustomerAddress.objects.create(
        customer=test_user_2,
        shopify_id=f"temp_address_test2_{int(datetime.now().timestamp())}",
        address1="456 Second Avenue",
        address2="Unit 7",
        city="Melbourne",
        province="Victoria",
        country="Australia",
        zip_code="3000",
        phone="+0987654321",
        first_name="Test",
        last_name="User Two",
        is_default=True
    )
    print(f"✅ Created address for Test User 2 with ID: {test_address_2.id}")
else:
    print(f"✅ Test User 2 {test_user_2_email} already exists (ID: {test_user_2.id})")

# Get some products to create orders with
products = ShopifyProduct.objects.filter(status='active')[:3]
if not products.exists():
    print("❌ No active products found for creating orders")
else:
    print(f"\n📦 Found {products.count()} products for creating orders:")
    for product in products:
        print(f"   - {product.title} (ID: {product.id})")

    # Create orders for test user 1
    print(f"\n📝 Creating orders for {test_user.email}...")
    
    # Order 1 - Recent order
    order_1 = ShopifyOrder.objects.create(
        customer=test_user,
        shopify_id=f"gid://shopify/Order/test_order_1_{int(datetime.now().timestamp())}",
        name=f"#TEST-{int(datetime.now().timestamp())}-1",
        email=test_user.email,
        financial_status="paid",
        fulfillment_status="fulfilled",
        total_price=Decimal("45.90"),
        subtotal_price=Decimal("39.90"),
        total_tax=Decimal("6.00"),
        currency="AUD",
        created_at=datetime.now() - timedelta(days=5),
        processed_at=datetime.now() - timedelta(days=5)
    )
    
    # Add line items to order 1
    for i, product in enumerate(products[:2]):
        ShopifyOrderLineItem.objects.create(
            order=order_1,
            product=product,
            shopify_id=f"test_line_item_{order_1.id}_{i}",
            title=product.title,
            quantity=1,
            price=Decimal("19.95"),
            total_discount=Decimal("0.00")
        )
    
    print(f"✅ Created Order 1: {order_1.name} (${order_1.total_price})")
    
    # Order 2 - Older order
    order_2 = ShopifyOrder.objects.create(
        customer=test_user,
        shopify_id=f"gid://shopify/Order/test_order_2_{int(datetime.now().timestamp())}",
        name=f"#TEST-{int(datetime.now().timestamp())}-2",
        email=test_user.email,
        financial_status="paid",
        fulfillment_status="unfulfilled",
        total_price=Decimal("29.95"),
        subtotal_price=Decimal("24.95"),
        total_tax=Decimal("5.00"),
        currency="AUD",
        created_at=datetime.now() - timedelta(days=15),
        processed_at=datetime.now() - timedelta(days=15)
    )
    
    # Add line item to order 2
    ShopifyOrderLineItem.objects.create(
        order=order_2,
        product=products[0],
        shopify_id=f"test_line_item_{order_2.id}_0",
        title=products[0].title,
        quantity=1,
        price=Decimal("24.95"),
        total_discount=Decimal("0.00")
    )
    
    print(f"✅ Created Order 2: {order_2.name} (${order_2.total_price})")
    
    # Create orders for test user 2
    print(f"\n📝 Creating orders for {test_user_2.email}...")
    
    # Order 3 - For Test User 2
    order_3 = ShopifyOrder.objects.create(
        customer=test_user_2,
        shopify_id=f"gid://shopify/Order/test_order_3_{int(datetime.now().timestamp())}",
        name=f"#TEST-{int(datetime.now().timestamp())}-3",
        email=test_user_2.email,
        financial_status="pending",
        fulfillment_status="unfulfilled",
        total_price=Decimal("67.85"),
        subtotal_price=Decimal("59.85"),
        total_tax=Decimal("8.00"),
        currency="AUD",
        created_at=datetime.now() - timedelta(days=2),
        processed_at=datetime.now() - timedelta(days=2)
    )
    
    # Add line items to order 3
    for i, product in enumerate(products):
        ShopifyOrderLineItem.objects.create(
            order=order_3,
            product=product,
            shopify_id=f"test_line_item_{order_3.id}_{i}",
            title=product.title,
            quantity=1,
            price=Decimal("19.95"),
            total_discount=Decimal("0.00")
        )
    
    print(f"✅ Created Order 3: {order_3.name} (${order_3.total_price})")

# Summary
print(f"\n" + "=" * 80)
print("SUMMARY OF CREATED TEST DATA")
print("=" * 80)

all_test_users = ShopifyCustomer.objects.filter(
    email__in=[target_email, test_user_2_email]
)

for user in all_test_users:
    print(f"\n👤 User: {user.email} (ID: {user.id})")
    print(f"   Name: {user.first_name} {user.last_name}")
    print(f"   Shopify ID: {user.shopify_id}")
    
    addresses = ShopifyCustomerAddress.objects.filter(customer=user)
    print(f"   Addresses: {addresses.count()}")
    for addr in addresses:
        print(f"     - {addr.address1}, {addr.city}, {addr.province}")
        print(f"       needs_shopify_push: {getattr(addr, 'needs_shopify_push', 'N/A')}")
    
    orders = ShopifyOrder.objects.filter(customer=user)
    print(f"   Orders: {orders.count()}")
    for order in orders:
        print(f"     - {order.name}: ${order.total_price} ({order.financial_status}/{order.fulfillment_status})")

print("\n✅ Test data creation complete!")
print("🔄 Ready for bidirectional sync testing")