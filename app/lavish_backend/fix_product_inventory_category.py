"""
Fix Product Category and Inventory Tracking Issues
===================================================

Issues to fix:
1. Category not syncing to Shopify
2. Inventory showing "not tracked" in Shopify
3. Variant stock not reflecting in Shopify
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def check_product_category_and_inventory():
    """Check Test Product 4 category and inventory"""
    
    print("=" * 80)
    print("CHECKING PRODUCT CATEGORY AND INVENTORY")
    print("=" * 80)
    
    # Find Test Product 4
    product = ShopifyProduct.objects.filter(title__icontains="test").order_by('-id').first()
    
    if not product:
        print("❌ Test product not found")
        return
    
    print(f"\n📦 Product: {product.title}")
    print(f"   ID: {product.id}")
    print(f"   Shopify ID: {product.shopify_id}")
    print(f"   Product Type (Category): {product.product_type or 'NOT SET'}")
    print(f"   Vendor: {product.vendor or 'NOT SET'}")
    print(f"   Status: {product.status}")
    
    # Check variants
    variants = product.variants.all()
    print(f"\n📊 Variants: {variants.count()}")
    
    for variant in variants:
        print(f"\n   Variant: {variant.title}")
        print(f"   - Shopify ID: {variant.shopify_id}")
        print(f"   - Price: ${variant.price}")
        print(f"   - SKU: {variant.sku}")
        print(f"   - Inventory Quantity: {variant.inventory_quantity}")
        print(f"   - Requires Shipping: {variant.requires_shipping}")
        
        # Check inventory item
        try:
            inv_item = ShopifyInventoryItem.objects.get(variant=variant)
            print(f"   - Inventory Item ID: {inv_item.shopify_id}")
            print(f"   - Tracked: {inv_item.tracked}")
            
            # Check inventory levels
            levels = ShopifyInventoryLevel.objects.filter(inventory_item=inv_item)
            print(f"   - Inventory Levels: {levels.count()}")
            for level in levels:
                print(f"     • Location: {level.location.name if level.location else 'Unknown'}")
                print(f"       Available: {level.available}")
        except ShopifyInventoryItem.DoesNotExist:
            print(f"   - ❌ No inventory item found")
    
    return product


def fix_product_in_shopify(product):
    """Fix product category and inventory in Shopify"""
    
    print("\n" + "=" * 80)
    print("FIXING IN SHOPIFY")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # First, query current state in Shopify
    query = """
    query getProduct($id: ID!) {
      product(id: $id) {
        id
        title
        productType
        vendor
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
                      available
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
    
    print(f"\n📊 Current state in Shopify:")
    print(f"   Product Type: {shopify_product.get('productType') or 'NOT SET'}")
    print(f"   Vendor: {shopify_product.get('vendor') or 'NOT SET'}")
    
    variants = shopify_product.get("variants", {}).get("edges", [])
    for edge in variants:
        variant = edge.get("node", {})
        inv_item = variant.get("inventoryItem", {})
        
        print(f"\n   Variant: {variant.get('title')}")
        print(f"   - Price: ${variant.get('price')}")
        print(f"   - SKU: {variant.get('sku')}")
        print(f"   - Inventory Quantity: {variant.get('inventoryQuantity')}")
        print(f"   - Tracked: {inv_item.get('tracked')}")
        
        levels = inv_item.get("inventoryLevels", {}).get("edges", [])
        for level_edge in levels:
            level = level_edge.get("node", {})
            location = level.get("location", {})
            print(f"   - Location: {location.get('name')}: {level.get('available')} available")
    
    # Fix 1: Update product type (category)
    if not shopify_product.get('productType') and product.product_type:
        print(f"\n🔧 Fixing product type...")
        
        update_mutation = """
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product {
              id
              productType
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "id": product.shopify_id,
                "productType": product.product_type
            }
        }
        
        result = client.execute_graphql_query(update_mutation, variables)
        
        if result.get("data", {}).get("productUpdate", {}).get("product"):
            print(f"   ✅ Product type updated to: {product.product_type}")
        else:
            errors = result.get("data", {}).get("productUpdate", {}).get("userErrors", [])
            print(f"   ❌ Failed: {errors}")
    
    # Fix 2: Enable inventory tracking for each variant
    for edge in variants:
        variant = edge.get("node", {})
        inv_item = variant.get("inventoryItem", {})
        
        if not inv_item.get("tracked"):
            print(f"\n🔧 Enabling inventory tracking for variant: {variant.get('title')}")
            
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
            
            variables = {
                "id": inv_item.get("id"),
                "input": {
                    "tracked": True
                }
            }
            
            result = client.execute_graphql_query(track_mutation, variables)
            
            if result.get("data", {}).get("inventoryItemUpdate", {}).get("inventoryItem"):
                print(f"   ✅ Inventory tracking enabled")
                
                # Now set the quantity
                django_variant = product.variants.filter(shopify_id=variant.get("id")).first()
                if django_variant and django_variant.inventory_quantity > 0:
                    print(f"   🔧 Setting inventory quantity to {django_variant.inventory_quantity}")
                    
                    # Get location ID
                    levels = inv_item.get("inventoryLevels", {}).get("edges", [])
                    if levels:
                        location_id = levels[0].get("node", {}).get("location", {}).get("id")
                        
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
                        
                        variables = {
                            "input": {
                                "reason": "correction",
                                "name": "available",
                                "quantities": [{
                                    "inventoryItemId": inv_item.get("id"),
                                    "locationId": location_id,
                                    "quantity": int(django_variant.inventory_quantity)
                                }]
                            }
                        }
                        
                        result = client.execute_graphql_query(set_mutation, variables)
                        
                        if result.get("data", {}).get("inventorySetQuantities", {}).get("inventoryAdjustmentGroup"):
                            print(f"   ✅ Inventory quantity set to {django_variant.inventory_quantity}")
                        else:
                            errors = result.get("data", {}).get("inventorySetQuantities", {}).get("userErrors", [])
                            print(f"   ❌ Failed to set quantity: {errors}")
            else:
                errors = result.get("data", {}).get("inventoryItemUpdate", {}).get("userErrors", [])
                print(f"   ❌ Failed: {errors}")


if __name__ == '__main__':
    product = check_product_category_and_inventory()
    
    if product:
        response = input("\n\nFix these issues in Shopify? (yes/no): ")
        if response.lower() == 'yes':
            fix_product_in_shopify(product)
            
            print("\n" + "=" * 80)
            print("✅ DONE - Check Shopify admin to verify")
            print("=" * 80)

