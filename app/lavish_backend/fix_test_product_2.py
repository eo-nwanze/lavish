"""
Fix Test Product 2 by resetting it to be created on Shopify
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct
from products.bidirectional_sync import ProductBidirectionalSync
from inventory.bidirectional_sync import InventoryBidirectionalSync

def fix_test_product_2():
    """Reset Test Product 2 and push to Shopify"""
    
    print("\n" + "="*80)
    print("🔧 FIXING TEST PRODUCT 2")
    print("="*80 + "\n")
    
    # Get Test Product 2
    product = ShopifyProduct.objects.filter(title__icontains='test product 2').first()
    
    if not product:
        print("❌ Test Product 2 not found")
        return
    
    print(f"Found: {product.title}")
    print(f"Current Shopify ID: {product.shopify_id}")
    print(f"Created in Django: {product.created_in_django}")
    
    # Clear fake IDs and mark for creation
    print("\n🔄 Clearing fake IDs and marking for creation...")
    
    product.shopify_id = None
    product.created_in_django = True
    product.needs_shopify_push = True
    product.shopify_push_error = None
    product.last_pushed_to_shopify = None
    product.save()
    
    # Clear variant IDs
    for variant in product.variants.all():
        print(f"   Clearing variant: {variant.title}")
        variant.shopify_id = None
        variant.save()
        
        # Clear inventory item IDs
        if hasattr(variant, 'inventory_item'):
            print(f"      Clearing inventory item")
            inv_item = variant.inventory_item
            inv_item.shopify_id = None
            inv_item.save()
            
            # Clear inventory level errors
            for level in inv_item.levels.all():
                level.needs_shopify_push = False
                level.shopify_push_error = None
                level.last_pushed_to_shopify = None
                level.save()
    
    print("✅ Cleared all fake IDs")
    
    # Now push to Shopify as a NEW product
    print("\n" + "="*80)
    print("🚀 PUSHING TO SHOPIFY")
    print("="*80 + "\n")
    
    sync_service = ProductBidirectionalSync()
    result = sync_service.push_product_to_shopify(product)
    
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('errors'):
        print(f"\n❌ ERRORS:")
        for key, value in result.get('errors', {}).items():
            print(f"   {key}: {value}")
    
    if result.get('success'):
        product.refresh_from_db()
        print(f"\n✅ NEW SHOPIFY ID: {product.shopify_id}")
        print(f"   Handle: {product.handle}")
        print(f"   Status: {product.status}")
        print(f"   Needs Push: {product.needs_shopify_push}")
        
        # Check variants
        print("\n📊 Variants:")
        for variant in product.variants.all():
            print(f"   - {variant.title}")
            print(f"     Shopify ID: {variant.shopify_id}")
            
            if hasattr(variant, 'inventory_item'):
                inv_item = variant.inventory_item
                print(f"     Inventory Item: {inv_item.shopify_id}")
                
                # Now push inventory levels
                print(f"\n     🔄 Pushing inventory levels...")
                for level in inv_item.levels.filter(available__gt=0):
                    print(f"        Location: {level.location.name} ({level.available} units)")
                    inv_sync = InventoryBidirectionalSync()
                    inv_result = inv_sync.push_inventory_to_shopify(level)
                    print(f"        Result: {'✅' if inv_result.get('success') else '❌'} {inv_result.get('message')}")
    
    print("\n" + "="*80)
    print("✅ COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    fix_test_product_2()
