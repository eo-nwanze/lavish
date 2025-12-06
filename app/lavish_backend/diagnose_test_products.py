"""
Diagnose Test Product 2 sync issues
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel
from products.bidirectional_sync import ProductBidirectionalSync
from inventory.bidirectional_sync import InventoryBidirectionalSync

def diagnose_test_products():
    """Check status of Test Product 1 and Test Product 2"""
    
    print("\n" + "="*80)
    print("🔍 DIAGNOSING TEST PRODUCTS")
    print("="*80 + "\n")
    
    # Find test products
    test_products = ShopifyProduct.objects.filter(title__icontains='test product').order_by('created_at')
    
    if not test_products.exists():
        print("❌ No test products found")
        return
    
    print(f"📦 Found {test_products.count()} test products\n")
    
    for product in test_products:
        print("="*80)
        print(f"📦 {product.title}")
        print("="*80)
        print(f"ID: {product.id}")
        print(f"Shopify ID: {product.shopify_id}")
        print(f"Handle: {product.handle}")
        print(f"Status: {product.status}")
        print(f"Created in Django: {product.created_in_django}")
        print(f"Needs Push: {product.needs_shopify_push}")
        print(f"Last Pushed: {product.last_pushed_to_shopify or 'Never'}")
        print(f"Push Error: {product.shopify_push_error or 'None'}")
        print(f"Created At: {product.created_at}")
        print(f"Updated At: {product.updated_at}")
        
        # Check variants
        variants = product.variants.all()
        print(f"\n📊 Variants: {variants.count()}")
        for variant in variants:
            print(f"   - {variant.title}")
            print(f"     Shopify ID: {variant.shopify_id}")
            print(f"     SKU: {variant.sku}")
            print(f"     Price: ${variant.price}")
            
            # Check inventory item
            if hasattr(variant, 'inventory_item'):
                inv_item = variant.inventory_item
                print(f"     ✅ Inventory Item: {inv_item.shopify_id}")
                print(f"        Tracked: {inv_item.tracked}")
                
                # Check inventory levels
                levels = inv_item.levels.all()
                print(f"        Inventory Levels: {levels.count()}")
                for level in levels:
                    print(f"           - {level.location.name}: {level.available} available")
                    print(f"             Needs Push: {level.needs_shopify_push}")
                    print(f"             Last Pushed: {level.last_pushed_to_shopify or 'Never'}")
                    print(f"             Error: {level.shopify_push_error or 'None'}")
            else:
                print(f"     ❌ NO INVENTORY ITEM")
        
        print()
    
    # Test sync for Test Product 2
    print("\n" + "="*80)
    print("🧪 TESTING SYNC FOR TEST PRODUCT 2")
    print("="*80 + "\n")
    
    test_product_2 = test_products.filter(title__icontains='test product 2').first()
    
    if not test_product_2:
        print("❌ Test Product 2 not found")
        return
    
    print(f"Testing sync for: {test_product_2.title}")
    print(f"Shopify ID: {test_product_2.shopify_id}")
    
    # Check if it's a temp ID
    if test_product_2.shopify_id and test_product_2.shopify_id.startswith('temp_'):
        print("\n⚠️ Product has TEMPORARY Shopify ID")
        print("   This means it was created in Django but not yet pushed to Shopify")
        print("\n🔄 Attempting to push to Shopify...")
        
        sync_service = ProductBidirectionalSync()
        result = sync_service.push_product_to_shopify(test_product_2)
        
        print(f"\n📊 RESULT:")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('errors'):
            print(f"Errors: {json.dumps(result.get('errors'), indent=2)}")
        
        if result.get('success'):
            test_product_2.refresh_from_db()
            print(f"\n✅ Updated Shopify ID: {test_product_2.shopify_id}")
            print(f"   Needs Push: {test_product_2.needs_shopify_push}")
    else:
        print("\n✅ Product has real Shopify ID")
        print("   Checking if update is needed...")
        
        if test_product_2.needs_shopify_push:
            print("   ⚠️ Product flagged for push, attempting update...")
            sync_service = ProductBidirectionalSync()
            result = sync_service.push_product_to_shopify(test_product_2)
            
            print(f"\n📊 RESULT:")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
        else:
            print("   ✅ Product is up to date")
    
    # Test inventory levels
    print("\n" + "="*80)
    print("📊 TESTING INVENTORY LEVELS FOR TEST PRODUCT 2")
    print("="*80 + "\n")
    
    test_product_2.refresh_from_db()
    variants = test_product_2.variants.all()
    
    for variant in variants:
        if hasattr(variant, 'inventory_item'):
            inv_item = variant.inventory_item
            levels = inv_item.levels.all()
            
            print(f"Variant: {variant.title}")
            print(f"Inventory Item: {inv_item.shopify_id}")
            print(f"Levels: {levels.count()}\n")
            
            for level in levels:
                print(f"   Location: {level.location.name}")
                print(f"   Available: {level.available}")
                print(f"   Needs Push: {level.needs_shopify_push}")
                
                if level.needs_shopify_push:
                    print(f"   🔄 Pushing to Shopify...")
                    sync_service = InventoryBidirectionalSync()
                    result = sync_service.push_inventory_to_shopify(level)
                    
                    print(f"   Result: {result.get('success')}")
                    print(f"   Message: {result.get('message')}")
                    
                    if result.get('adjustment_group'):
                        changes = result['adjustment_group'].get('changes', [])
                        for change in changes:
                            print(f"      - {change['name']}: delta={change['delta']}")
                print()
    
    print("\n" + "="*80)
    print("✅ DIAGNOSIS COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    diagnose_test_products()
