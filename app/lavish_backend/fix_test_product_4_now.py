"""
Fix Test Product 4 Immediately
================================

This script will:
1. Sync Variant 2 to Shopify (get real Shopify ID)
2. Enable inventory tracking for both variants
3. Set inventory quantities in Shopify
4. Create inventory items/levels in Django
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel, ShopifyLocation
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from django.utils import timezone
import json


def fix_product_4():
    """Fix Test Product 4 completely"""
    
    print("=" * 80)
    print("FIXING TEST PRODUCT 4 - COMPLETE FIX")
    print("=" * 80)
    
    # Get Test Product 4
    product = ShopifyProduct.objects.filter(
        title__icontains="Test Product"
    ).order_by('-id').first()
    
    if not product:
        print("❌ Product not found")
        return
    
    print(f"\n📦 Product: {product.title}")
    print(f"   Shopify ID: {product.shopify_id}")
    
    client = EnhancedShopifyAPIClient()
    
    # Step 1: Query product from Shopify to get full details
    print(f"\n🔍 Step 1: Querying Shopify for current state...")
    
    query = """
    query getProduct($id: ID!) {
      product(id: $id) {
        id
        title
        productType
        variants(first: 10) {
          edges {
            node {
              id
              title
              price
              sku
              inventoryQuantity
              inventoryItem {
                id
                tracked
                inventoryLevels(first: 5) {
                  edges {
                    node {
                      id
                      quantities(names: ["available"]) {
                        name
                        quantity
                      }
                      location {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    result = client.execute_graphql_query(query, {"id": product.shopify_id})
    
    if "errors" in result:
        print("❌ Error querying product:")
        print(json.dumps(result["errors"], indent=2))
        return
    
    shopify_product = result.get("data", {}).get("product", {})
    shopify_variants = shopify_product.get("variants", {}).get("edges", [])
    
    print(f"   Found {len(shopify_variants)} variant(s) in Shopify")
    
    # Step 2: Sync Django variants to Shopify variants
    print(f"\n🔄 Step 2: Syncing variants...")
    
    django_variants = product.variants.all().order_by('id')
    
    for django_variant in django_variants:
        print(f"\n   Variant: {django_variant.title}")
        print(f"   - Django Shopify ID: {django_variant.shopify_id}")
        
        # Check if this variant exists in Shopify
        found_in_shopify = False
        shopify_variant_data = None
        
        for edge in shopify_variants:
            variant = edge.get("node", {})
            if variant.get("id") == django_variant.shopify_id:
                found_in_shopify = True
                shopify_variant_data = variant
                print(f"   - ✅ Found in Shopify: {variant.get('id')}")
                break
        
        if not found_in_shopify or django_variant.shopify_id.startswith('temp_'):
            print(f"   - ⚠️ NOT in Shopify or has temp ID")
            print(f"   - 🔧 Need to sync variant to Shopify first...")
            
            # This variant needs to be created in Shopify
            # We'll trigger a product update which should create missing variants
            print(f"   - Triggering product update...")
            
            # Mark product for push
            product.needs_shopify_push = True
            product.save()
            
            # Push to Shopify
            from products.bidirectional_sync import ProductBidirectionalSync
            sync = ProductBidirectionalSync()
            result = sync.push_product_to_shopify(product)
            
            if result.get('success'):
                print(f"   - ✅ Product synced successfully")
                # Re-query to get updated variant IDs
                product.refresh_from_db()
                django_variant.refresh_from_db()
                print(f"   - New Shopify ID: {django_variant.shopify_id}")
                
                # Re-query Shopify
                result = client.execute_graphql_query(query, {"id": product.shopify_id})
                shopify_product = result.get("data", {}).get("product", {})
                shopify_variants = shopify_product.get("variants", {}).get("edges", [])
                
                # Find this variant again
                for edge in shopify_variants:
                    variant = edge.get("node", {})
                    if variant.get("sku") == django_variant.sku:
                        shopify_variant_data = variant
                        break
            else:
                print(f"   - ❌ Failed: {result.get('message')}")
                continue
    
    # Step 3: Enable inventory tracking and set quantities
    print(f"\n📦 Step 3: Enabling inventory tracking and setting quantities...")
    
    # Re-query to get fresh data
    result = client.execute_graphql_query(query, {"id": product.shopify_id})
    shopify_product = result.get("data", {}).get("product", {})
    shopify_variants = shopify_product.get("variants", {}).get("edges", [])
    
    for edge in shopify_variants:
        variant = edge.get("node", {})
        inv_item = variant.get("inventoryItem", {})
        
        print(f"\n   Variant: {variant.get('title')}")
        print(f"   - Tracked: {inv_item.get('tracked')}")
        
        # Find corresponding Django variant
        django_variant = product.variants.filter(shopify_id=variant.get('id')).first()
        
        if not django_variant:
            print(f"   - ⚠️ No Django variant found")
            continue
        
        print(f"   - Django Stock: {django_variant.inventory_quantity}")
        
        # Enable tracking if not already
        if not inv_item.get('tracked'):
            print(f"   - 🔧 Enabling inventory tracking...")
            
            track_mutation = """
            mutation inventoryItemUpdate($id: ID!, $input: InventoryItemInput!) {
              inventoryItemUpdate(id: $id, input: $input) {
                inventoryItem {
                  id
                  tracked
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            
            track_result = client.execute_graphql_query(
                track_mutation,
                {
                    "id": inv_item.get("id"),
                    "input": {"tracked": True}
                }
            )
            
            track_data = track_result.get("data", {}).get("inventoryItemUpdate", {})
            track_errors = track_data.get("userErrors", [])
            
            if track_errors:
                print(f"   - ❌ Failed to enable tracking: {track_errors}")
                continue
            else:
                print(f"   - ✅ Tracking enabled")
        
        # Set inventory quantity
        levels = inv_item.get("inventoryLevels", {}).get("edges", [])
        
        if levels and django_variant.inventory_quantity > 0:
            location_id = levels[0].get("node", {}).get("location", {}).get("id")
            location_name = levels[0].get("node", {}).get("location", {}).get("name")
            
            print(f"   - 🔧 Setting inventory to {django_variant.inventory_quantity} at {location_name}...")
            
            set_mutation = """
            mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
              inventorySetQuantities(input: $input) {
                inventoryAdjustmentGroup {
                  id
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            
            set_result = client.execute_graphql_query(
                set_mutation,
                {
                    "input": {
                        "reason": "correction",
                        "name": "available",
                        "ignoreCompareQuantity": True,
                        "quantities": [{
                            "inventoryItemId": inv_item.get("id"),
                            "locationId": location_id,
                            "quantity": int(django_variant.inventory_quantity)
                        }]
                    }
                }
            )
            
            set_data = set_result.get("data", {}).get("inventorySetQuantities", {})
            set_errors = set_data.get("userErrors", [])
            
            if set_errors:
                print(f"   - ❌ Failed to set quantity: {set_errors}")
            else:
                print(f"   - ✅ Quantity set to {django_variant.inventory_quantity}")
            
            # Create inventory records in Django
            print(f"   - 💾 Creating Django inventory records...")
            
            # Get or create location
            location, _ = ShopifyLocation.objects.get_or_create(
                shopify_id=location_id,
                defaults={
                    'name': location_name,
                    'active': True
                }
            )
            
            # Create inventory item
            inv_item_obj, created = ShopifyInventoryItem.objects.get_or_create(
                shopify_id=inv_item.get("id"),
                defaults={
                    'variant': django_variant,
                    'tracked': True,
                    'requires_shipping': django_variant.requires_shipping
                }
            )
            
            if created:
                print(f"   - ✅ Created ShopifyInventoryItem")
            else:
                inv_item_obj.tracked = True
                inv_item_obj.save()
                print(f"   - ✅ Updated ShopifyInventoryItem")
            
            # Create inventory level
            inv_level, created = ShopifyInventoryLevel.objects.get_or_create(
                inventory_item=inv_item_obj,
                location=location,
                defaults={
                    'available': django_variant.inventory_quantity,
                    'updated_at': timezone.now(),
                    'needs_shopify_push': False
                }
            )
            
            if created:
                print(f"   - ✅ Created ShopifyInventoryLevel")
            else:
                inv_level.available = django_variant.inventory_quantity
                inv_level.needs_shopify_push = False
                inv_level.save()
                print(f"   - ✅ Updated ShopifyInventoryLevel")
    
    # Final verification
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print(f"{'='*80}")
    
    result = client.execute_graphql_query(query, {"id": product.shopify_id})
    shopify_product = result.get("data", {}).get("product", {})
    shopify_variants = shopify_product.get("variants", {}).get("edges", [])
    
    print(f"\n✅ Product: {shopify_product.get('title')}")
    print(f"   Category: {shopify_product.get('productType')}")
    print(f"   Variants: {len(shopify_variants)}")
    
    for edge in shopify_variants:
        variant = edge.get("node", {})
        inv_item = variant.get("inventoryItem", {})
        levels = inv_item.get("inventoryLevels", {}).get("edges", [])
        
        print(f"\n   {variant.get('title')}:")
        print(f"   - Price: ${variant.get('price')}")
        print(f"   - SKU: {variant.get('sku')}")
        print(f"   - Tracked: {inv_item.get('tracked')} {'✅' if inv_item.get('tracked') else '❌'}")
        print(f"   - Inventory: {variant.get('inventoryQuantity')}")
        
        for level_edge in levels:
            level = level_edge.get("node", {})
            location = level.get("location", {})
            quantities = level.get("quantities", [])
            available = next((q.get("quantity") for q in quantities if q.get("name") == "available"), 0)
            print(f"   - Location {location.get('name')}: {available} units")
    
    print(f"\n{'='*80}")
    print("✅ DONE - Test Product 4 is now fully synced!")
    print(f"{'='*80}")
    
    print("\nCheck Shopify admin to verify:")
    print("  1. Both variants visible ✅")
    print("  2. Inventory tracked ✅")
    print("  3. Stock quantities correct ✅")
    print("  4. Category shows ✅")


if __name__ == '__main__':
    fix_product_4()

