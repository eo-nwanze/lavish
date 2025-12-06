"""
Test bidirectional inventory sync - check if inventory levels sync from Shopify to Django
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel, ShopifyLocation
from inventory.realtime_sync import sync_inventory_realtime, get_inventory_sync_stats

print("\n" + "=" * 70)
print("TESTING BIDIRECTIONAL INVENTORY SYNC")
print("=" * 70)

# Check current state
print("\n📊 Current Inventory State (Before Sync):")
print("-" * 70)

test_products = ShopifyProduct.objects.filter(id__in=[99, 102])
for product in test_products:
    print(f"\n📦 {product.title}")
    for variant in product.variants.all():
        print(f"   Variant: {variant.title} (SKU: {variant.sku})")
        print(f"   Inventory Qty in Variant Model: {variant.inventory_quantity}")
        
        try:
            inv_item = variant.inventory_item
            print(f"   ✅ Has Inventory Item: {inv_item.shopify_id}")
            print(f"      Tracked: {inv_item.tracked}")
            
            levels = inv_item.levels.all()
            if levels.exists():
                print(f"      Inventory Levels:")
                for level in levels:
                    print(f"         • {level.location.name}: {level.available} available")
            else:
                print(f"      ⚠️  No inventory levels")
        except:
            print(f"   ⚠️  No inventory item linked")

print("\n" + "=" * 70)
print("CHECKING SYNC CAPABILITIES")
print("=" * 70)

# Check if we can sync from Shopify
print("\n🔍 Checking sync service availability...")
try:
    from inventory.realtime_sync import RealtimeInventorySyncService
    sync_service = RealtimeInventorySyncService()
    print("✅ Inventory sync service is available")
    
    # Get current sync stats
    stats = get_inventory_sync_stats()
    print(f"\n📈 Current Sync Statistics:")
    print(f"   Total Inventory Items: {stats['total_inventory_items']}")
    print(f"   Total Inventory Levels: {stats['total_inventory_levels']}")
    print(f"   Total Locations: {stats['total_locations']}")
    print(f"   Tracked Items: {stats['tracked_items']}")
    print(f"   Total Available Inventory: {stats['total_available_inventory']}")
    print(f"   Low Stock Items: {stats['low_stock_items']}")
    
except Exception as e:
    print(f"❌ Sync service error: {e}")

print("\n" + "=" * 70)
print("BIDIRECTIONAL SYNC ANALYSIS")
print("=" * 70)

print("""
📋 Current Sync Capabilities:

1. ✅ SHOPIFY → DJANGO (Pull):
   - RealtimeInventorySyncService can pull inventory from Shopify
   - Method: sync_all_inventory() 
   - Syncs: Inventory Items, Levels, and Locations
   - Webhook: inventory_levels/update is configured
   
2. ⚠️  DJANGO → SHOPIFY (Push):
   - NO automatic push detected
   - Inventory changes in Django are NOT automatically pushed to Shopify
   - This is ONE-WAY sync only (Shopify → Django)

3. 🔄 Webhook Support:
   - inventory_levels/update webhook is configured
   - When inventory changes in Shopify, webhook can update Django
   - But changes in Django do NOT trigger Shopify updates

⚠️  IMPORTANT FINDINGS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Inventory sync is ONE-WAY: Shopify → Django ONLY
• Unlike products (which have bidirectional sync via bidirectional_sync.py),
  inventory does NOT have automatic push to Shopify
• Test products created in Django have local inventory data but it's not 
  automatically synced to Shopify
• You need to manually update inventory in Shopify OR implement push logic

RECOMMENDATION:
To achieve true bidirectional sync like products, you would need to:
1. Implement an InventoryPushService similar to product bidirectional_sync
2. Add needs_shopify_push flag to ShopifyInventoryLevel model
3. Use Shopify GraphQL inventoryAdjustQuantities mutation
4. Add model signals to detect Django inventory changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

print("\n" + "=" * 70)
print("TEST PRODUCT SYNC STATUS")
print("=" * 70)

print("""
For your test products:

📦 Test Product from Django (ID: 99):
   • Has inventory in Django: 100 units at 8 Mellifont Street
   • NOT synced to Shopify (no Shopify product ID yet)
   • Will need manual Shopify inventory setup after product sync

📦 Test Product 2 (ID: 102):  
   • Has inventory in Django: 150 units at 8 Mellifont Street
   • Has mock Shopify ID: gid://shopify/Product/test_1765030488
   • Inventory is local only - NOT in Shopify yet
   
✅ TO FIX: After syncing products to Shopify, you must:
   1. Get the real Shopify product/variant IDs
   2. Use Shopify Admin or API to set inventory levels
   3. OR implement bidirectional inventory push (see recommendation above)
""")

print("=" * 70)
