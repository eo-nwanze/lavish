"""
Test creating a product via the admin save flow
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from products.bidirectional_sync import ProductBidirectionalSync
from django.utils import timezone

def test_product_creation():
    """Test creating a product like the admin does"""
    
    print("\n" + "="*80)
    print("🧪 TESTING PRODUCT CREATION")
    print("="*80 + "\n")
    
    # Create product
    product = ShopifyProduct(
        title="Test Product 3 - Full Admin Flow",
        description="Testing product creation with variant",
        vendor="Lavish Library",
        product_type="Test Products",
        status="ACTIVE",
        created_in_django=True
    )
    
    print("1️⃣ Creating product...")
    product.save()
    print(f"   ✅ Product created: {product.title}")
    print(f"   ID: {product.id}")
    print(f"   Shopify ID: {product.shopify_id}")
    print(f"   Handle: {product.handle}")
    
    # Create variant
    print("\n2️⃣ Creating variant...")
    variant = ShopifyProductVariant(
        product=product,
        title="Default Title",
        sku="TEST-3-001",
        price=29.99,
        compare_at_price=39.99,
        inventory_quantity=10
    )
    variant.save()
    print(f"   ✅ Variant created: {variant.title}")
    print(f"   Shopify ID: {variant.shopify_id}")
    print(f"   SKU: {variant.sku}")
    print(f"   Price: ${variant.price}")
    
    # Now push to Shopify
    print("\n3️⃣ Pushing to Shopify...")
    sync_service = ProductBidirectionalSync()
    result = sync_service.push_product_to_shopify(product)
    
    print(f"\n📊 RESULT:")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('errors'):
        print(f"\n❌ ERRORS:")
        for key, value in result.get('errors', {}).items():
            print(f"   {key}: {value}")
    
    if result.get('success'):
        product.refresh_from_db()
        variant.refresh_from_db()
        
        print(f"\n✅ SYNCED TO SHOPIFY:")
        print(f"   Product Shopify ID: {product.shopify_id}")
        print(f"   Variant Shopify ID: {variant.shopify_id}")
        print(f"   Handle: {product.handle}")
        print(f"   Status: {product.status}")
        
        # Check inventory item
        if hasattr(variant, 'inventory_item'):
            inv_item = variant.inventory_item
            print(f"\n📦 Inventory Item:")
            print(f"   Shopify ID: {inv_item.shopify_id}")
            print(f"   SKU: {inv_item.sku}")
            print(f"   Tracked: {inv_item.tracked}")
            
            # Check levels
            levels = inv_item.levels.all()
            print(f"\n   Inventory Levels: {levels.count()}")
            for level in levels:
                print(f"      - {level.location.name}: {level.available} available")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_product_creation()
