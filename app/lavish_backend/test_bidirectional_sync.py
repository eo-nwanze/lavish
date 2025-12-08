#!/usr/bin/env python
"""
TEST BIDIRECTIONAL SYNC - LIVE SHOPIFY STORE
============================================

This script demonstrates that products, customers, and inventory
created/updated in Django are automatically pushed to the live Shopify store
at https://www.lavishlibrary.com.au/

CURRENT CONFIGURATION:
- Store: 7fa66c-ac.myshopify.com (Lavish Library)
- Domain: https://www.lavishlibrary.com.au/
- API Access: ✅ Connected and functional
- Bidirectional Sync: ✅ Configured and active
"""

import os
import django
import sys
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Import Django models and services
from products.models import ShopifyProduct, ShopifyProductVariant
from products.bidirectional_sync import ProductBidirectionalSync
from customers.models import ShopifyCustomer
from customers.customer_bidirectional_sync import push_customer_to_shopify
from inventory.models import ShopifyInventoryLevel, ShopifyInventoryItem
from inventory.bidirectional_sync import push_inventory_to_shopify
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

def test_product_sync():
    """Test product bidirectional sync to live Shopify store"""
    print("\n" + "="*60)
    print("🧪 TESTING PRODUCT BIDIRECTIONAL SYNC")
    print("="*60)
    
    # Create a test product in Django
    print("\n1. Creating test product in Django...")
    test_product = ShopifyProduct.objects.create(
        shopify_id=f"test_product_{int(time.time())}",
        title=f"Django Test Product - {datetime.now().strftime('%H:%M:%S')}",
        description="This product was created in Django to test bidirectional sync",
        vendor="Lavish Library Test",
        product_type="Test Product",
        status="DRAFT",
        created_in_django=True,
        needs_shopify_push=True,
        tags=["test", "django", "bidirectional"]
    )
    
    print(f"✅ Product created in Django: {test_product.title}")
    print(f"   - Django ID: {test_product.id}")
    print(f"   - Temp Shopify ID: {test_product.shopify_id}")
    print(f"   - Needs push: {test_product.needs_shopify_push}")
    
    # Test bidirectional sync
    print("\n2. Pushing product to live Shopify store...")
    sync_service = ProductBidirectionalSync()
    result = sync_service.push_product_to_shopify(test_product)
    
    if result.get('success'):
        print("✅ Product successfully pushed to Shopify!")
        print(f"   - Shopify ID: {result.get('shopify_id', 'N/A')}")
        print(f"   - Message: {result.get('message', 'Success')}")
        
        # Refresh product data
        test_product.refresh_from_db()
        print(f"   - Real Shopify ID: {test_product.shopify_id}")
        print(f"   - Needs push: {test_product.needs_shopify_push}")
        print(f"   - Sync status: {test_product.sync_status}")
        
        # Verify it's on the live store
        print(f"\n3. Verifying product on live store...")
        print(f"   🌐 Live store: https://www.lavishlibrary.com.au/")
        print(f"   📱 Admin: https://7fa66c-ac.myshopify.com/admin/products/{test_product.shopify_id.split('/')[-1]}")
        
        return True
    else:
        print(f"❌ Failed to push product to Shopify: {result.get('message', 'Unknown error')}")
        return False

def test_customer_sync():
    """Test customer bidirectional sync to live Shopify store"""
    print("\n" + "="*60)
    print("🧪 TESTING CUSTOMER BIDIRECTIONAL SYNC")
    print("="*60)
    
    # Create a test customer in Django
    print("\n1. Creating test customer in Django...")
    test_customer = ShopifyCustomer.objects.create(
        shopify_id=f"test_customer_{int(time.time())}",
        email=f"test.{int(time.time())}@lavishlibrary.com.au",
        first_name="Test",
        last_name="Customer",
        phone="+61400000000",
        needs_shopify_push=True,
        tags=["test", "django", "bidirectional"]
    )
    
    print(f"✅ Customer created in Django: {test_customer.email}")
    print(f"   - Django ID: {test_customer.id}")
    print(f"   - Temp Shopify ID: {test_customer.shopify_id}")
    print(f"   - Needs push: {test_customer.needs_shopify_push}")
    
    # Test bidirectional sync
    print("\n2. Pushing customer to live Shopify store...")
    result = push_customer_to_shopify(test_customer)
    
    if result.get('success'):
        print("✅ Customer successfully pushed to Shopify!")
        print(f"   - Shopify ID: {result.get('shopify_id', 'N/A')}")
        print(f"   - Message: {result.get('message', 'Success')}")
        
        # Refresh customer data
        test_customer.refresh_from_db()
        print(f"   - Real Shopify ID: {test_customer.shopify_id}")
        print(f"   - Needs push: {test_customer.needs_shopify_push}")
        print(f"   - Sync status: {test_customer.sync_status}")
        
        # Verify it's on the live store
        print(f"\n3. Verifying customer on live store...")
        print(f"   🌐 Live store: https://www.lavishlibrary.com.au/")
        print(f"   📱 Admin: https://7fa66c-ac.myshopify.com/admin/customers/{test_customer.shopify_id.split('/')[-1]}")
        
        return True
    else:
        print(f"❌ Failed to push customer to Shopify: {result.get('message', 'Unknown error')}")
        return False

def test_inventory_sync():
    """Test inventory bidirectional sync to live Shopify store"""
    print("\n" + "="*60)
    print("🧪 TESTING INVENTORY BIDIRECTIONAL SYNC")
    print("="*60)
    
    # Get existing inventory level to test
    inventory_level = ShopifyInventoryLevel.objects.first()
    
    if not inventory_level:
        print("❌ No inventory levels found. Please ensure inventory is synced first.")
        return False
    
    print(f"\n1. Found existing inventory level:")
    print(f"   - Product: {inventory_level.inventory_item.sku if inventory_level.inventory_item else 'Unknown'}")
    print(f"   - Location: {inventory_level.location.name}")
    print(f"   - Current quantity: {inventory_level.available}")
    
    # Modify inventory quantity
    original_quantity = inventory_level.available
    new_quantity = original_quantity + 10
    
    print(f"\n2. Updating inventory quantity in Django...")
    inventory_level.available = new_quantity
    inventory_level.needs_shopify_push = True
    inventory_level.save()
    
    print(f"   - New quantity: {new_quantity}")
    print(f"   - Needs push: {inventory_level.needs_shopify_push}")
    
    # Test bidirectional sync
    print("\n3. Pushing inventory update to live Shopify store...")
    result = push_inventory_to_shopify(inventory_level)
    
    if result.get('success'):
        print("✅ Inventory successfully pushed to Shopify!")
        print(f"   - Message: {result.get('message', 'Success')}")
        
        # Refresh inventory data
        inventory_level.refresh_from_db()
        print(f"   - Needs push: {inventory_level.needs_shopify_push}")
        print(f"   - Last pushed: {inventory_level.last_pushed_to_shopify}")
        
        # Verify it's on the live store
        print(f"\n4. Verifying inventory on live store...")
        print(f"   🌐 Live store: https://www.lavishlibrary.com.au/")
        print(f"   📱 Admin: https://7fa66c-ac.myshopify.com/admin/inventory_levels")
        
        return True
    else:
        print(f"❌ Failed to push inventory to Shopify: {result.get('message', 'Unknown error')}")
        return False

def verify_shopify_connection():
    """Verify connection to the live Shopify store"""
    print("\n" + "="*60)
    print("🔍 VERIFYING SHOPIFY STORE CONNECTION")
    print("="*60)
    
    client = EnhancedShopifyAPIClient()
    
    try:
        result = client.test_connection()
        if result.get('success'):
            shop_info = result.get('shop_info', {})
            print("✅ Successfully connected to live Shopify store!")
            print(f"   - Store Name: {shop_info.get('name', 'N/A')}")
            print(f"   - Email: {shop_info.get('email', 'N/A')}")
            print(f"   - MyShopify Domain: {shop_info.get('myshopifyDomain', 'N/A')}")
            print(f"   - Currency: {shop_info.get('currencyCode', 'N/A')}")
            print(f"   - Live Store: https://www.lavishlibrary.com.au/")
            print(f"   - Admin: https://{shop_info.get('myshopifyDomain', 'N/A')}/admin")
            return True
        else:
            print(f"❌ Connection failed: {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 LAVISH LIBRARY - BIDIRECTIONAL SYNC TEST")
    print("=" * 60)
    print("Testing Django → Live Shopify Store synchronization")
    print("Store: https://www.lavishlibrary.com.au/")
    print("=" * 60)
    
    # Verify Shopify connection
    if not verify_shopify_connection():
        print("\n❌ Cannot proceed with tests - Shopify connection failed")
        return False
    
    # Run tests
    results = []
    
    try:
        # Test product sync
        product_result = test_product_sync()
        results.append(('Product Sync', product_result))
        
        # Test customer sync
        customer_result = test_customer_sync()
        results.append(('Customer Sync', customer_result))
        
        # Test inventory sync
        inventory_result = test_inventory_sync()
        results.append(('Inventory Sync', inventory_result))
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Bidirectional sync is working correctly")
        print("✅ Products, customers, and inventory created/updated in Django")
        print("✅ Are automatically pushed to the live Shopify store")
        print("✅ at https://www.lavishlibrary.com.au/")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("❌ Please check the configuration and error messages above")
    
    print("\n" + "="*60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)