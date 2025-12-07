"""
Fix Product Sync Issue
=======================

When a product is deleted in Shopify but still exists in Django with an old Shopify ID,
it causes "Product does not exist" errors on update.

Solution: Clear the shopify_id and recreate the product in Shopify.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct
from products.bidirectional_sync import ProductBidirectionalSync
from django.utils import timezone
import time

def fix_product(product_id=None):
    """Fix a product with invalid Shopify ID"""
    
    if product_id:
        try:
            product = ShopifyProduct.objects.get(id=product_id)
        except ShopifyProduct.DoesNotExist:
            print(f"❌ Product #{product_id} not found")
            return
    else:
        # Get product with sync error
        product = ShopifyProduct.objects.filter(
            needs_shopify_push=True,
            shopify_push_error__icontains="Validation errors"
        ).order_by('-updated_at').first()
        
        if not product:
            print("✅ No products with sync errors found")
            return
    
    print("=" * 80)
    print(f"FIXING PRODUCT: {product.title}")
    print("=" * 80)
    
    print(f"\nCurrent state:")
    print(f"  ID: {product.id}")
    print(f"  Shopify ID: {product.shopify_id}")
    print(f"  Status: {product.status}")
    print(f"  Needs Push: {product.needs_shopify_push}")
    print(f"  Error: {product.shopify_push_error}")
    
    # Check if shopify_id exists in Shopify
    print(f"\n🔍 Checking if product exists in Shopify...")
    
    from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
    client = EnhancedShopifyAPIClient()
    
    query = """
    query getProduct($id: ID!) {
      product(id: $id) {
        id
        title
        status
      }
    }
    """
    
    try:
        result = client.execute_graphql_query(query, {"id": product.shopify_id})
        
        if result.get("data", {}).get("product"):
            print("  ✅ Product exists in Shopify")
            print("  Error might be something else - check mutations")
            return
        else:
            print("  ❌ Product NOT found in Shopify (was deleted)")
    except Exception as e:
        print(f"  ⚠️ Error checking: {e}")
    
    # Solution: Clear shopify_id and recreate
    print(f"\n💡 SOLUTION: Clear old Shopify ID and recreate product")
    response = input("\nProceed? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled")
        return
    
    # Clear the shopify_id
    old_shopify_id = product.shopify_id
    timestamp = int(time.time())
    product.shopify_id = f"temp_{timestamp}"
    product.created_in_django = True
    product.needs_shopify_push = True
    product.shopify_push_error = ""
    product.save()
    
    print(f"\n✅ Cleared old Shopify ID: {old_shopify_id}")
    print(f"   New temp ID: {product.shopify_id}")
    
    # Now push to Shopify (will create new product)
    print(f"\n🚀 Creating new product in Shopify...")
    
    sync = ProductBidirectionalSync()
    result = sync.push_product_to_shopify(product)
    
    if result.get('success'):
        product.refresh_from_db()
        print(f"\n✅ SUCCESS!")
        print(f"   New Shopify ID: {product.shopify_id}")
        print(f"   Status: Synced")
    else:
        print(f"\n❌ FAILED: {result.get('message')}")
        if 'errors' in result:
            for error in result['errors']:
                print(f"   - {error.get('field')}: {error.get('message')}")


def fix_all_broken_products():
    """Fix all products with invalid Shopify IDs"""
    
    print("\n" + "=" * 80)
    print("FIXING ALL PRODUCTS WITH SYNC ERRORS")
    print("=" * 80)
    
    broken_products = ShopifyProduct.objects.filter(
        needs_shopify_push=True,
        shopify_push_error__icontains="error"
    ).order_by('-updated_at')
    
    count = broken_products.count()
    
    if count == 0:
        print("\n✅ No products need fixing!")
        return
    
    print(f"\nFound {count} product(s) with errors")
    
    for i, product in enumerate(broken_products, 1):
        print(f"\n{i}/{count}. {product.title}")
        print(f"   Error: {product.shopify_push_error[:50]}...")
        
        response = input(f"   Fix this product? (yes/no/quit): ")
        
        if response.lower() == 'quit':
            break
        elif response.lower() == 'yes':
            fix_product(product.id)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            fix_all_broken_products()
        else:
            product_id = int(sys.argv[1])
            fix_product(product_id)
    else:
        # Find Test Product 3
        product = ShopifyProduct.objects.filter(
            title__icontains="Test Product 3"
        ).first()
        
        if product:
            fix_product(product.id)
        else:
            print("Product not found - checking for any products with errors...")
            fix_product()

