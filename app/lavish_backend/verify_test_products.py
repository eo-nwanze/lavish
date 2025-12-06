"""
Verify test products with inventory
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel

test_products = ShopifyProduct.objects.filter(id__in=[99, 102]).prefetch_related(
    'variants__inventory_item__levels__location'
)

print("\n" + "=" * 60)
print("TEST PRODUCTS WITH INVENTORY DETAILS")
print("=" * 60)

for p in test_products:
    print(f"\n📦 Product: {p.title}")
    print(f"   ID: {p.id}")
    print(f"   Status: {p.status}")
    print(f"   Handle: {p.handle}")
    print(f"   Shopify ID: {p.shopify_id or 'Not synced yet'}")
    
    for v in p.variants.all():
        print(f"\n   📋 Variant: {v.title}")
        print(f"      SKU: {v.sku}")
        print(f"      Price: ${v.price}")
        print(f"      Inventory Qty: {v.inventory_quantity}")
        print(f"      Management: {v.inventory_management}")
        
        try:
            inv_item = v.inventory_item
            print(f"      ✅ Inventory Item: {inv_item.shopify_id}")
            print(f"      Tracked: {inv_item.tracked}")
            
            levels = inv_item.levels.all()
            if levels:
                print(f"\n      📍 Inventory Levels:")
                for level in levels:
                    print(f"         • {level.location.name}: {level.available} units")
            else:
                print(f"      ⚠️  No inventory levels set")
        except:
            print(f"      ⚠️  No inventory item linked")

print("\n" + "=" * 60)
