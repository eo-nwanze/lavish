"""
Fix Inventory Tracking for Products Created in Django
This script fetches inventory item data from Shopify and enables tracking
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel, ShopifyLocation
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from django.utils.dateparse import parse_datetime

print("\n" + "=" * 70)
print("FIXING INVENTORY TRACKING FOR DJANGO-CREATED PRODUCTS")
print("=" * 70)

client = EnhancedShopifyAPIClient()

# Find products that don't have inventory items
products_without_inventory = ShopifyProduct.objects.filter(
    shopify_id__isnull=False
).exclude(
    shopify_id__startswith='temp_'
).exclude(
    shopify_id__startswith='test_'
)

print(f'\nChecking {products_without_inventory.count()} products...')

fixed_count = 0
error_count = 0

for product in products_without_inventory:
    print(f'\n[Product] {product.title}')
    
    # Check each variant
    for variant in product.variants.all():
        # Check if variant has inventory item
        try:
            inv_item = variant.inventory_item
            print(f'   [OK] Variant already has inventory item')
            continue
        except:
            pass
        
        # Variant needs inventory item - fetch from Shopify
        print(f'   [Fetching] inventory item from Shopify...')
        
        try:
            # Extract variant ID from GID
            variant_id = variant.shopify_id.split('/')[-1]
            
            # Query Shopify for variant details including inventory item
            query = """
            query getVariantInventory($id: ID!) {
              productVariant(id: $id) {
                id
                inventoryItem {
                  id
                  sku
                  tracked
                  inventoryLevels(first: 10) {
                    edges {
                      node {
                        id
                        quantities(names: "available") {
                          quantity
                          name
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
            """
            
            variables = {"id": variant.shopify_id}
            result = client.execute_graphql_query(query, variables)
            
            if "errors" in result:
                print(f'   [ERROR] GraphQL Error: {result["errors"]}')
                error_count += 1
                continue
            
            variant_data = result.get('data', {}).get('productVariant', {})
            inventory_item_data = variant_data.get('inventoryItem', {})
            
            if not inventory_item_data or not inventory_item_data.get('id'):
                print(f'   [WARNING] No inventory item found in Shopify')
                error_count += 1
                continue
            
            # Create/update inventory item
            inventory_item, created = ShopifyInventoryItem.objects.update_or_create(
                shopify_id=inventory_item_data['id'],
                defaults={
                    'sku': inventory_item_data.get('sku', variant.sku),
                    'tracked': inventory_item_data.get('tracked', False),
                    'product_title': product.title,
                    'variant_title': variant.title,
                    'store_domain': '7fa66c-ac.myshopify.com',
                }
            )
            
            # Link to variant
            variant.inventory_item = inventory_item
            variant.save()
            
            action = "Created" if created else "Updated"
            print(f'   [SUCCESS] {action} inventory item: {inventory_item.shopify_id}')
            print(f'      Tracked: {inventory_item.tracked}')
            
            # Now enable tracking if not already tracked
            if not inventory_item.tracked:
                print(f'   [Enabling] inventory tracking...')
                
                # Use GraphQL mutation to enable tracking
                mutation = """
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
                
                variables = {
                    "id": inventory_item.shopify_id,
                    "input": {
                        "tracked": True
                    }
                }
                
                update_result = client.execute_graphql_query(mutation, variables)
                
                if "errors" not in update_result:
                    data = update_result.get('data', {}).get('inventoryItemUpdate', {})
                    user_errors = data.get('userErrors', [])
                    
                    if not user_errors:
                        inventory_item.tracked = True
                        inventory_item.save()
                        print(f'   [SUCCESS] Tracking enabled!')
                    else:
                        print(f'   [WARNING] Tracking enable failed: {user_errors}')
                else:
                    print(f'   [WARNING] GraphQL error: {update_result["errors"]}')
            
            # Sync inventory levels
            levels_data = inventory_item_data.get('inventoryLevels', {}).get('edges', [])
            for edge in levels_data:
                level_node = edge.get('node', {})
                location_data = level_node.get('location', {})
                
                # Get or create location
                location, loc_created = ShopifyLocation.objects.get_or_create(
                    shopify_id=location_data['id'],
                    defaults={
                        'name': location_data.get('name', 'Unknown'),
                        'store_domain': '7fa66c-ac.myshopify.com',
                    }
                )
                
                # Get available quantity from quantities field
                quantities = level_node.get('quantities', [])
                available = 0
                for qty in quantities:
                    if qty.get('name') == 'available':
                        available = qty.get('quantity', 0)
                        break
                
                # Create/update inventory level
                level, level_created = ShopifyInventoryLevel.objects.update_or_create(
                    inventory_item=inventory_item,
                    location=location,
                    defaults={
                        'available': available,
                    }
                )
                
                print(f'      • {location.name}: {level.available} units')
            
            fixed_count += 1
            
        except Exception as e:
            print(f'   [ERROR] Error: {str(e)}')
            error_count += 1

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f'[SUCCESS] Fixed: {fixed_count} variants')
print(f'[ERROR] Errors: {error_count} variants')
print("=" * 70)
