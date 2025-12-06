"""
Script to fix inventory for test product and create a new test product with inventory
"""
import django
import os
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel, ShopifyLocation
from django.utils import timezone

print("=" * 60)
print("FIXING TEST PRODUCT INVENTORY & CREATING NEW TEST PRODUCT")
print("=" * 60)

# Get the existing test product
test_product = ShopifyProduct.objects.get(id=99)
print(f"\n1. Found existing test product: {test_product.title}")
print(f"   Product ID: {test_product.id}")
print(f"   Status: {test_product.status}")

# Get its variant
variant = test_product.variants.first()
if variant:
    print(f"\n2. Found variant: {variant.title}")
    print(f"   Variant ID: {variant.id}")
    print(f"   SKU: {variant.sku}")
    print(f"   Current inventory_quantity: {variant.inventory_quantity}")
    
    # Update variant inventory settings
    variant.inventory_quantity = 100
    variant.inventory_management = 'shopify'
    variant.inventory_policy = 'deny'
    variant.save()
    print(f"   ✅ Updated variant inventory_quantity to 100")
    
    # Check if inventory item exists
    try:
        inv_item = variant.inventory_item
        print(f"\n3. Found existing inventory item: {inv_item.shopify_id}")
    except:
        # Create inventory item
        inv_item = ShopifyInventoryItem.objects.create(
            shopify_id=f"test_inv_item_{variant.id}",
            sku=variant.sku or f"TEST-SKU-{variant.id}",
            tracked=True,
            requires_shipping=True,
            variant=variant,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        print(f"\n3. ✅ Created inventory item: {inv_item.shopify_id}")
    
    # Get primary location (8 Mellifont Street)
    primary_location = ShopifyLocation.objects.get(id=2)
    print(f"\n4. Using location: {primary_location.name}")
    
    # Create or update inventory level
    inv_level, created = ShopifyInventoryLevel.objects.update_or_create(
        inventory_item=inv_item,
        location=primary_location,
        defaults={
            'available': 100,
            'updated_at': timezone.now()
        }
    )
    action = "Created" if created else "Updated"
    print(f"   ✅ {action} inventory level: {inv_level.available} units available")

print("\n" + "=" * 60)
print("CREATING NEW TEST PRODUCT WITH INVENTORY")
print("=" * 60)

# Create new test product
now = timezone.now()
timestamp = now.strftime("%Y-%m-%d %H:%M")

new_product = ShopifyProduct.objects.create(
    shopify_id=f"gid://shopify/Product/test_{int(now.timestamp())}",
    title=f"Test Product 2 - {timestamp}",
    handle=f"test-product-2-{int(now.timestamp())}",
    description="This is a test product created from Django with full inventory setup.",
    product_type="Test Products",
    vendor="Lavish Library",
    status="ACTIVE",
    created_at=now,
    updated_at=now,
    published_at=now
)
print(f"\n5. ✅ Created new product: {new_product.title}")
print(f"   Product ID: {new_product.id}")
print(f"   Handle: {new_product.handle}")

# Create variant for new product
new_variant = ShopifyProductVariant.objects.create(
    product=new_product,
    shopify_id=f"gid://shopify/ProductVariant/test_{int(now.timestamp())}",
    title="Default Title",
    sku=f"TEST-2-{int(now.timestamp())}",
    price=29.99,
    compare_at_price=39.99,
    inventory_quantity=150,
    inventory_management='shopify',
    inventory_policy='deny',
    weight=0.5,
    weight_unit='kg',
    available=True,
    requires_shipping=True,
    taxable=True,
    position=1,
    created_at=now,
    updated_at=now
)
print(f"\n6. ✅ Created variant: {new_variant.title}")
print(f"   Variant ID: {new_variant.id}")
print(f"   SKU: {new_variant.sku}")
print(f"   Price: ${new_variant.price}")
print(f"   Inventory: {new_variant.inventory_quantity}")

# Create inventory item for new product
new_inv_item = ShopifyInventoryItem.objects.create(
    shopify_id=f"gid://shopify/InventoryItem/test_{int(now.timestamp())}",
    sku=new_variant.sku,
    tracked=True,
    requires_shipping=True,
    cost=15.00,
    variant=new_variant,
    created_at=now,
    updated_at=now
)
print(f"\n7. ✅ Created inventory item: {new_inv_item.shopify_id}")
print(f"   SKU: {new_inv_item.sku}")
print(f"   Cost: ${new_inv_item.cost}")

# Create inventory levels for all locations
locations = ShopifyLocation.objects.filter(active=True)
print(f"\n8. Creating inventory levels for {locations.count()} locations:")

for location in locations:
    inv_level = ShopifyInventoryLevel.objects.create(
        inventory_item=new_inv_item,
        location=location,
        available=150 if location.id == 2 else 0,  # 150 at primary location
        updated_at=now
    )
    print(f"   ✅ {location.name}: {inv_level.available} units")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\n✅ Fixed inventory for: {test_product.title}")
print(f"   - Variant inventory: 100 units")
print(f"   - Inventory item created")
print(f"   - Inventory level at {primary_location.name}: 100 units")

print(f"\n✅ Created new product: {new_product.title}")
print(f"   - Product ID: {new_product.id}")
print(f"   - Variant with SKU: {new_variant.sku}")
print(f"   - Price: ${new_variant.price}")
print(f"   - Inventory: 150 units at primary location")
print(f"   - Status: {new_product.status}")

print(f"\n✨ Both products are ready for Shopify sync!")
print("=" * 60)
