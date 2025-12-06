"""
Enhanced test script with detailed API response logging
"""

import os
import django
import sys
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import ShopifyInventoryLevel, ShopifyInventoryItem, ShopifyLocation
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from django.utils import timezone

def test_inventory_sync_detailed():
    """Test with detailed API response logging"""
    
    print("\n" + "="*80)
    print("🔍 DETAILED INVENTORY SYNC TEST")
    print("="*80 + "\n")
    
    # Get a test inventory level
    test_level = ShopifyInventoryLevel.objects.select_related(
        'inventory_item', 'location'
    ).first()
    
    if not test_level:
        print("❌ No inventory levels found")
        return
    
    print(f"📦 Testing with:")
    print(f"   Inventory Item ID: {test_level.inventory_item.shopify_id}")
    print(f"   Location ID: {test_level.location.shopify_id}")
    print(f"   Current Available: {test_level.available}")
    print(f"   Setting to: 15\n")
    
    # Prepare GraphQL mutation
    mutation = """
    mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
      inventorySetQuantities(input: $input) {
        inventoryAdjustmentGroup {
          id
          reason
          changes {
            name
            delta
            quantityAfterChange
          }
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
            "ignoreCompareQuantity": True,
            "quantities": [{
                "inventoryItemId": test_level.inventory_item.shopify_id,
                "locationId": test_level.location.shopify_id,
                "quantity": 15
            }]
        }
    }
    
    print("📤 Sending GraphQL request:")
    print(json.dumps(variables, indent=2))
    print()
    
    # Execute request
    client = EnhancedShopifyAPIClient()
    result = client.execute_graphql_query(mutation, variables)
    
    print("📥 FULL API RESPONSE:")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80)
    print()
    
    # Parse response
    if "errors" in result:
        print("❌ GraphQL Errors:", result["errors"])
        return
    
    data = result.get("data", {}).get("inventorySetQuantities", {})
    user_errors = data.get("userErrors", [])
    adjustment_group = data.get("inventoryAdjustmentGroup")
    
    print("📊 PARSED RESULTS:")
    print(f"   User Errors: {user_errors if user_errors else 'None'}")
    print(f"   Adjustment Group: {adjustment_group}")
    print()
    
    if adjustment_group:
        print("✅ SUCCESS - Inventory updated!")
        test_level.available = 15
        test_level.needs_shopify_push = False
        test_level.last_pushed_to_shopify = timezone.now()
        test_level.save()
    else:
        print("⚠️ WARNING - No adjustment group returned")
        print("   This could mean:")
        print("   1. The quantity was already at that value")
        print("   2. The inventory item doesn't allow updates")
        print("   3. The location is not active")
        print()
        
        # Check current Shopify quantity
        print("🔍 Checking current quantity on Shopify...")
        query = """
        query inventoryItem($id: ID!) {
          inventoryItem(id: $id) {
            id
            sku
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
        """
        
        check_result = client.execute_graphql_query(query, {
            "id": test_level.inventory_item.shopify_id
        })
        
        print("\n📦 Current Shopify Inventory:")
        print(json.dumps(check_result, indent=2))

if __name__ == "__main__":
    test_inventory_sync_detailed()
