"""
Check Test Product Inventory Status
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant

print("\n" + "=" * 70)
print("TEST PRODUCT INVENTORY CHECK")
print("=" * 70)

test_prod = ShopifyProduct.objects.filter(title__icontains='Test Product from Django').first()

if test_prod:
    print(f'\n📦 Product: {test_prod.title}')
    print(f'   Shopify ID: {test_prod.shopify_id}')
    
    variant = test_prod.variants.first()
    if variant:
        print(f'\n📋 Variant:')
        print(f'   Title: {variant.title}')
        print(f'   Shopify ID: {variant.shopify_id}')
        print(f'   Inventory Quantity: {variant.inventory_quantity}')
        print(f'   Inventory Policy: {variant.inventory_policy}')
        print(f'   Inventory Management: {variant.inventory_management}')
        
        try:
            inv = variant.inventory_item
            print(f'\n📊 Inventory Item:')
            print(f'   Shopify ID: {inv.shopify_id}')
            print(f'   SKU: {inv.sku}')
            print(f'   Tracked: {inv.tracked}')
            print(f'   Cost: {inv.cost or "N/A"}')
            
            # Check inventory levels
            levels = inv.levels.all()
            if levels.exists():
                print(f'\n📍 Inventory Levels:')
                for level in levels:
                    print(f'   • {level.location.name}: {level.available} available')
                    print(f'     needs_shopify_push: {level.needs_shopify_push}')
            else:
                print(f'\n⚠️  No inventory levels set')
                
        except Exception as e:
            print(f'\n❌ No inventory item linked: {e}')
    else:
        print('\n❌ No variants found')
else:
    print('\n❌ Test product not found')

print("\n" + "=" * 70)
