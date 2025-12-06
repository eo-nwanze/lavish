"""
Add orders to test users with existing products
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
print("ADDING ORDERS TO TEST USERS")
print("=" * 80)

# Get test users
test_user = ShopifyCustomer.objects.get(email="testuser@example.com")
test_user_2 = ShopifyCustomer.objects.get(email="testuser2@example.com")

print(f"📋 Test User 1: {test_user.email} (ID: {test_user.id})")
print(f"📋 Test User 2: {test_user_2.email} (ID: {test_user_2.id})")

# Get available products
products = ShopifyProduct.objects.all()[:5]  # Get any products
print(f"\n📦 Available products: {products.count()}")

if products.exists():
    for i, product in enumerate(products, 1):
        print(f"   {i}. {product.title} (ID: {product.id}, Status: {product.status})")
        # Check variants
        variants = ShopifyProductVariant.objects.filter(product=product)[:2]
        for variant in variants:
            print(f"      Variant: {variant.title} - ${variant.price}")
else:
    print("❌ No products found!")
    
    # Create a simple test product
    print("\n📝 Creating test product...")
    test_product = ShopifyProduct.objects.create(
        shopify_id=f"gid://shopify/Product/test_product_{int(datetime.now().timestamp())}",
        title="Test Book Collection",
        body_html="<p>A test book collection for order testing</p>",
        status="active",
        product_type="Books",
        vendor="Lavish Library",
        handle=f"test-book-collection-{int(datetime.now().timestamp())}",
        published_scope="web",
        created_at=timezone.now(),
        updated_at=timezone.now()
    )
    
    # Create variant for the product
    test_variant = ShopifyProductVariant.objects.create(
        product=test_product,
        shopify_id=f"gid://shopify/ProductVariant/test_variant_{int(datetime.now().timestamp())}",
        title="Default Title",
        price=Decimal("29.95"),
        compare_at_price=Decimal("39.95"),
        position=1,
        inventory_management="shopify",
        inventory_policy="deny",
        fulfillment_service="manual",
        inventory_quantity=100,
        weight=500.0,
        weight_unit="g",
        created_at=timezone.now(),
        updated_at=timezone.now()
    )
    
    print(f"✅ Created test product: {test_product.title}")
    print(f"✅ Created test variant: {test_variant.title} - ${test_variant.price}")
    
    products = [test_product]

# Now create orders
print(f"\n📝 Creating orders...")

# Order 1 for test user 1 - Recent paid order
try:
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
        billing_address_first_name=test_user.first_name,
        billing_address_last_name=test_user.last_name,
        billing_address_address1="123 Test Street",
        billing_address_city="Test City",
        billing_address_province="Test State",
        billing_address_country="Australia",
        billing_address_zip="12345",
        created_at=timezone.now() - timedelta(days=5),
        updated_at=timezone.now() - timedelta(days=5),
        processed_at=timezone.now() - timedelta(days=5)
    )
    
    # Add line items
    variant = ShopifyProductVariant.objects.filter(product=products[0]).first()
    if variant:
        ShopifyOrderLineItem.objects.create(
            order=order_1,
            product=products[0],
            variant=variant,
            shopify_id=f"test_line_item_{order_1.id}_1",
            title=products[0].title,
            variant_title=variant.title,
            quantity=1,
            price=variant.price,
            total_discount=Decimal("0.00")
        )
    
    print(f"✅ Created Order 1: {order_1.name} (${order_1.total_price}) - {order_1.financial_status}")
    
except Exception as e:
    print(f"❌ Error creating order 1: {e}")

# Order 2 for test user 1 - Pending order
try:
    order_2 = ShopifyOrder.objects.create(
        customer=test_user,
        shopify_id=f"gid://shopify/Order/test_order_2_{int(datetime.now().timestamp())}",
        name=f"#TEST-{int(datetime.now().timestamp())}-2",
        email=test_user.email,
        financial_status="pending",
        fulfillment_status="unfulfilled",
        total_price=Decimal("29.95"),
        subtotal_price=Decimal("29.95"),
        total_tax=Decimal("0.00"),
        currency="AUD",
        billing_address_first_name=test_user.first_name,
        billing_address_last_name=test_user.last_name,
        billing_address_address1="123 Test Street",
        billing_address_city="Test City",
        billing_address_province="Test State",
        billing_address_country="Australia",
        billing_address_zip="12345",
        created_at=timezone.now() - timedelta(days=1),
        updated_at=timezone.now() - timedelta(days=1),
        processed_at=timezone.now() - timedelta(days=1)
    )
    
    # Add line item
    variant = ShopifyProductVariant.objects.filter(product=products[0]).first()
    if variant:
        ShopifyOrderLineItem.objects.create(
            order=order_2,
            product=products[0],
            variant=variant,
            shopify_id=f"test_line_item_{order_2.id}_1",
            title=products[0].title,
            variant_title=variant.title,
            quantity=1,
            price=variant.price,
            total_discount=Decimal("0.00")
        )
    
    print(f"✅ Created Order 2: {order_2.name} (${order_2.total_price}) - {order_2.financial_status}")
    
except Exception as e:
    print(f"❌ Error creating order 2: {e}")

# Order 3 for test user 2 - Recent order
try:
    order_3 = ShopifyOrder.objects.create(
        customer=test_user_2,
        shopify_id=f"gid://shopify/Order/test_order_3_{int(datetime.now().timestamp())}",
        name=f"#TEST-{int(datetime.now().timestamp())}-3",
        email=test_user_2.email,
        financial_status="paid",
        fulfillment_status="unfulfilled",
        total_price=Decimal("67.85"),
        subtotal_price=Decimal("59.85"),
        total_tax=Decimal("8.00"),
        currency="AUD",
        billing_address_first_name=test_user_2.first_name,
        billing_address_last_name=test_user_2.last_name,
        billing_address_address1="456 Second Avenue",
        billing_address_city="Melbourne",
        billing_address_province="Victoria",
        billing_address_country="Australia",
        billing_address_zip="3000",
        created_at=timezone.now() - timedelta(hours=3),
        updated_at=timezone.now() - timedelta(hours=3),
        processed_at=timezone.now() - timedelta(hours=3)
    )
    
    # Add line items
    variant = ShopifyProductVariant.objects.filter(product=products[0]).first()
    if variant:
        # Add 2 items
        ShopifyOrderLineItem.objects.create(
            order=order_3,
            product=products[0],
            variant=variant,
            shopify_id=f"test_line_item_{order_3.id}_1",
            title=products[0].title,
            variant_title=variant.title,
            quantity=2,
            price=variant.price,
            total_discount=Decimal("0.00")
        )
    
    print(f"✅ Created Order 3: {order_3.name} (${order_3.total_price}) - {order_3.financial_status}")
    
except Exception as e:
    print(f"❌ Error creating order 3: {e}")

# Summary
print(f"\n" + "=" * 80)
print("ORDER CREATION SUMMARY")
print("=" * 80)

for user in [test_user, test_user_2]:
    orders = ShopifyOrder.objects.filter(customer=user).order_by('-created_at')
    print(f"\n👤 {user.email}:")
    print(f"   Orders: {orders.count()}")
    for order in orders:
        line_items = ShopifyOrderLineItem.objects.filter(order=order)
        print(f"   📦 {order.name}: ${order.total_price} ({order.financial_status}/{order.fulfillment_status})")
        print(f"      Items: {line_items.count()}")
        for item in line_items:
            print(f"        - {item.title} x{item.quantity} @ ${item.price}")

print("\n✅ Orders created successfully!")
print("🔄 Ready for address change and bidirectional sync testing")