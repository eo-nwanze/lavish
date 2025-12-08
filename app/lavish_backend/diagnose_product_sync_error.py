"""
Diagnose Product Sync Errors
=============================

This script helps identify why products fail to sync to Shopify.
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct
from products.bidirectional_sync import ProductBidirectionalSync


def diagnose_product(product_id=None):
    """Diagnose why a product failed to sync"""
    
    if product_id:
        try:
            product = ShopifyProduct.objects.get(id=product_id)
        except ShopifyProduct.DoesNotExist:
            print(f"❌ Product #{product_id} not found")
            return
    else:
        # Get most recently updated product that needs push
        product = ShopifyProduct.objects.filter(
            needs_shopify_push=True
        ).order_by('-updated_at').first()
        
        if not product:
            print("✅ No products need syncing")
            return
    
    print("=" * 80)
    print(f"DIAGNOSING PRODUCT: {product.title}")
    print("=" * 80)
    
    print(f"\nProduct Details:")
    print(f"  ID: {product.id}")
    print(f"  Title: {product.title}")
    print(f"  Shopify ID: {product.shopify_id}")
    print(f"  Status: {product.status}")
    print(f"  Price: ${product.price}")
    print(f"  Compare at Price: ${product.compare_at_price or 'None'}")
    print(f"  SKU: {product.sku or 'None'}")
    print(f"  Barcode: {product.barcode or 'None'}")
    print(f"  Weight: {product.weight}")
    print(f"  Weight Unit: {product.weight_unit}")
    print(f"  Inventory Policy: {product.inventory_policy}")
    print(f"  Inventory Tracked: {product.inventory_tracked}")
    print(f"  Created in Django: {product.created_in_django}")
    print(f"  Needs Push: {product.needs_shopify_push}")
    
    # Try to push and capture detailed errors
    print("\n" + "=" * 80)
    print("ATTEMPTING PUSH TO SHOPIFY")
    print("=" * 80)
    
    sync = ProductBidirectionalSync()
    
    # Manually build the GraphQL mutation to see what we're sending
    print("\nBuilding GraphQL mutation...")
    
    if product.shopify_id:
        # Update
        print(f"  Operation: UPDATE (ID: {product.shopify_id})")
        
        mutation = """
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product {
              id
              title
              status
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
                "title": product.title,
                "descriptionHtml": product.description or "",
                "status": product.status,
                "vendor": product.vendor or "",
                "productType": product.product_type or "",
                "tags": product.tags.split(',') if product.tags else [],
            }
        }
    else:
        # Create
        print(f"  Operation: CREATE")
        
        mutation = """
        mutation productCreate($input: ProductInput!) {
          productCreate(input: $input) {
            product {
              id
              title
              status
              variants(first: 1) {
                edges {
                  node {
                    id
                    price
                  }
                }
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
                "title": product.title,
                "descriptionHtml": product.description or "",
                "status": product.status,
                "vendor": product.vendor or "",
                "productType": product.product_type or "",
                "tags": product.tags.split(',') if product.tags else [],
                "variants": [{
                    "price": str(product.price),
                    "sku": product.sku or "",
                    "barcode": product.barcode or "",
                    "weight": float(product.weight) if product.weight else 0.0,
                    "weightUnit": product.weight_unit,
                    "inventoryPolicy": product.inventory_policy,
                    "inventoryManagement": "SHOPIFY" if product.inventory_tracked else None,
                }]
            }
        }
    
    print("\nVariables being sent:")
    print(json.dumps(variables, indent=2))
    
    # Execute the mutation
    print("\n" + "=" * 80)
    print("EXECUTING GRAPHQL MUTATION")
    print("=" * 80)
    
    from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
    client = EnhancedShopifyAPIClient()
    
    try:
        result = client.execute_graphql_query(mutation, variables)
        
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
        # Check for errors
        if "errors" in result:
            print("\n❌ GraphQL Errors:")
            for error in result["errors"]:
                print(f"   - {error.get('message')}")
                if 'locations' in error:
                    print(f"     Location: {error['locations']}")
                if 'extensions' in error:
                    print(f"     Extensions: {error['extensions']}")
        
        # Check for user errors
        if product.shopify_id:
            user_errors = result.get("data", {}).get("productUpdate", {}).get("userErrors", [])
        else:
            user_errors = result.get("data", {}).get("productCreate", {}).get("userErrors", [])
        
        if user_errors:
            print("\n❌ Validation Errors:")
            for error in user_errors:
                print(f"   Field: {error.get('field')}")
                print(f"   Message: {error.get('message')}")
                print()
        
        if not result.get("errors") and not user_errors:
            print("\n✅ Push successful!")
            
            if product.shopify_id:
                updated_product = result.get("data", {}).get("productUpdate", {}).get("product", {})
            else:
                updated_product = result.get("data", {}).get("productCreate", {}).get("product", {})
            
            print(f"   Shopify ID: {updated_product.get('id')}")
            print(f"   Title: {updated_product.get('title')}")
            print(f"   Status: {updated_product.get('status')}")
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    issues = []
    
    if not product.title or len(product.title.strip()) == 0:
        issues.append("❌ Title is required")
    
    if product.price is None or product.price < 0:
        issues.append("❌ Price must be >= 0")
    
    if product.weight is None or product.weight < 0:
        issues.append("❌ Weight must be >= 0")
    
    if product.weight_unit not in ['GRAMS', 'KILOGRAMS', 'OUNCES', 'POUNDS']:
        issues.append(f"❌ Invalid weight unit: {product.weight_unit}")
    
    if product.status not in ['ACTIVE', 'DRAFT', 'ARCHIVED']:
        issues.append(f"❌ Invalid status: {product.status}")
    
    if product.inventory_policy not in ['DENY', 'CONTINUE']:
        issues.append(f"❌ Invalid inventory policy: {product.inventory_policy}")
    
    if issues:
        print("\nFound issues:")
        for issue in issues:
            print(f"  {issue}")
        print("\nFix these in Django admin and save again.")
    else:
        print("\n✅ No obvious issues found")
        print("   Check GraphQL errors above for details")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        product_id = int(sys.argv[1])
        diagnose_product(product_id)
    else:
        # Get the product that was just saved
        product = ShopifyProduct.objects.filter(
            title__icontains="Test Product 3"
        ).order_by('-updated_at').first()
        
        if product:
            print(f"Found product: {product.title} (ID: {product.id})")
            diagnose_product(product.id)
        else:
            print("Looking for most recent product needing push...")
            diagnose_product()




