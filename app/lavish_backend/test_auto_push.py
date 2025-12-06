"""
Test creating a product and customer with auto-push to Shopify
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant
from customers.models import ShopifyCustomer
from products.bidirectional_sync import ProductBidirectionalSync
from customers.customer_bidirectional_sync import CustomerBidirectionalSync

def test_auto_push():
    """Test creating records and auto-pushing to Shopify"""
    
    print("\n" + "="*80)
    print("🧪 TESTING AUTO-PUSH TO SHOPIFY")
    print("="*80 + "\n")
    
    # Test 1: Create Product
    print("1️⃣ Creating Product...")
    product = ShopifyProduct(
        title="Auto-Push Test Product",
        description="Testing auto-push to Shopify on creation",
        vendor="Lavish Library",
        product_type="Test Products",
        status="ACTIVE",
        created_in_django=True
    )
    product.save()
    print(f"   ✅ Product created locally")
    print(f"   ID: {product.id}")
    print(f"   Shopify ID: {product.shopify_id}")
    print(f"   Needs Push: {product.needs_shopify_push}")
    
    # Create variant
    variant = ShopifyProductVariant(
        product=product,
        title="Default Title",
        sku="AUTO-PUSH-001",
        price=19.99,
        inventory_quantity=5
    )
    variant.save()
    print(f"   ✅ Variant created: {variant.shopify_id}")
    
    # Now push to Shopify
    if product.needs_shopify_push:
        print(f"\n   🔄 Pushing to Shopify...")
        sync_service = ProductBidirectionalSync()
        result = sync_service.push_product_to_shopify(product)
        
        print(f"\n   📊 RESULT:")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('success'):
            product.refresh_from_db()
            variant.refresh_from_db()
            print(f"\n   ✅ SYNCED TO SHOPIFY:")
            print(f"   Product Shopify ID: {product.shopify_id}")
            print(f"   Variant Shopify ID: {variant.shopify_id}")
            print(f"   Handle: {product.handle}")
        else:
            print(f"\n   ❌ ERRORS: {result.get('errors', result.get('error'))}")
    
    # Test 2: Create Customer
    print("\n" + "="*80)
    print("2️⃣ Creating Customer...")
    customer = ShopifyCustomer(
        email="autopush.test@example.com",
        first_name="AutoPush",
        last_name="TestCustomer",
        phone="+61400111222",
        verified_email=True,
        accepts_marketing=True
    )
    customer.save()
    print(f"   ✅ Customer created locally")
    print(f"   ID: {customer.id}")
    print(f"   Shopify ID: {customer.shopify_id}")
    print(f"   Needs Push: {customer.needs_shopify_push}")
    
    # Now push to Shopify
    if customer.needs_shopify_push:
        print(f"\n   🔄 Pushing to Shopify...")
        sync_service = CustomerBidirectionalSync()
        result = sync_service.push_customer_to_shopify(customer)
        
        print(f"\n   📊 RESULT:")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('success'):
            customer.refresh_from_db()
            print(f"\n   ✅ SYNCED TO SHOPIFY:")
            print(f"   Customer Shopify ID: {customer.shopify_id}")
            print(f"   Email: {customer.email}")
        else:
            print(f"\n   ❌ ERRORS: {result.get('errors', result.get('error'))}")
    
    print("\n" + "="*80)
    print("✅ AUTO-PUSH TEST COMPLETE")
    print("="*80 + "\n")
    
    # Clean up
    print("🧹 Cleaning up...")
    if product.shopify_id and product.shopify_id.startswith('gid://shopify/Product/'):
        print(f"   Product synced to Shopify: {product.shopify_id}")
    product.delete()
    
    if customer.shopify_id and customer.shopify_id.startswith('gid://shopify/Customer/'):
        print(f"   Customer synced to Shopify: {customer.shopify_id}")
    customer.delete()
    print("   ✅ Test data deleted\n")

if __name__ == "__main__":
    test_auto_push()
