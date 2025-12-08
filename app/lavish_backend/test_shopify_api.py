#!/usr/bin/env python
"""
Simple Shopify API Test Script
Tests the core functionality without complex synchronization
"""

import os
import sys
import json
from datetime import datetime

# Add the project path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from shopify_integration.models import ShopifyStore

def test_shopify_api():
    """Test basic Shopify API functionality"""
    print("=" * 60)
    print("🛍️  SHOPIFY API TEST")
    print("=" * 60)
    
    # Initialize client
    client = EnhancedShopifyAPIClient()
    
    # Test 1: Connection
    print("\n1. Testing API Connection...")
    connection_result = client.test_connection()
    if connection_result['success']:
        print(f"✅ Connected to: {connection_result['shop_info']['name']}")
        print(f"   Email: {connection_result['shop_info']['email']}")
        print(f"   Domain: {connection_result['shop_info']['myshopifyDomain']}")
    else:
        print(f"❌ Connection failed: {connection_result['message']}")
        return False
    
    # Test 2: Get Shop Info
    print("\n2. Testing Shop Info...")
    try:
        shop_info = client.get_shop_info()
        print(f"✅ Shop: {shop_info['name']}")
        print(f"   Currency: {shop_info['currencyCode']}")
    except Exception as e:
        print(f"❌ Shop info failed: {e}")
        return False
    
    # Test 3: Get Products (small sample)
    print("\n3. Testing Product Retrieval...")
    try:
        products = client.fetch_all_products(limit=5)
        print(f"✅ Retrieved {len(products)} products")
        if products:
            print(f"   Sample: {products[0]['title']}")
    except Exception as e:
        print(f"❌ Product retrieval failed: {e}")
        return False
    
    # Test 4: Get Customers (small sample)
    print("\n4. Testing Customer Retrieval...")
    try:
        customers = client.fetch_all_customers(limit=5)
        print(f"✅ Retrieved {len(customers)} customers")
        if customers:
            print(f"   Sample: {customers[0]['firstName']} {customers[0]['lastName']} ({customers[0]['email']})")
    except Exception as e:
        print(f"❌ Customer retrieval failed: {e}")
        return False
    
    # Test 5: Get Orders (small sample)
    print("\n5. Testing Order Retrieval...")
    try:
        orders = client.fetch_all_orders(limit=5)
        print(f"✅ Retrieved {len(orders)} orders")
        if orders:
            print(f"   Sample: {orders[0]['name']} - {orders[0]['totalPriceSet']['shopMoney']['currencyCode']} {orders[0]['totalPriceSet']['shopMoney']['amount']}")
    except Exception as e:
        print(f"❌ Order retrieval failed: {e}")
        return False
    
    # Test 6: Get Locations
    print("\n6. Testing Location Retrieval...")
    try:
        locations = client.fetch_all_locations()
        print(f"✅ Retrieved {len(locations)} locations")
        if locations:
            print(f"   Sample: {locations[0]['name']}")
    except Exception as e:
        print(f"❌ Location retrieval failed: {e}")
        return False
    
    # Test 7: REST API Methods
    print("\n7. Testing REST API Methods...")
    try:
        # Test get_customers method
        customers_rest = client.get_customers(limit=5)
        print(f"✅ REST API: Retrieved {len(customers_rest.get('customers', []))} customers")
    except Exception as e:
        print(f"❌ REST API failed: {e}")
        return False
    
    # Test 8: Store Record
    print("\n8. Testing Store Record...")
    try:
        store = ShopifyStore.objects.get(store_domain='7fa66c-ac.myshopify.com')
        print(f"✅ Store record: {store.store_name}")
        print(f"   API Version: {store.api_version}")
        print(f"   Currency: {store.currency}")
    except Exception as e:
        print(f"❌ Store record failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Shopify API is fully functional")
    print("=" * 60)
    
    return True

def show_store_stats():
    """Display current store statistics"""
    print("\n📊 STORE STATISTICS")
    print("-" * 30)
    
    client = EnhancedShopifyAPIClient()
    
    try:
        # Get counts
        products = client.fetch_all_products(limit=100)
        customers = client.fetch_all_customers(limit=100)
        orders = client.fetch_all_orders(limit=100)
        locations = client.fetch_all_locations()
        
        print(f"Products: {len(products)}+")
        print(f"Customers: {len(customers)}+")
        print(f"Orders: {len(orders)}+")
        print(f"Locations: {len(locations)}")
        
        # Get inventory levels
        inventory_levels = client.fetch_all_inventory_levels(limit=100)
        print(f"Inventory Levels: {len(inventory_levels)}+")
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")

if __name__ == "__main__":
    success = test_shopify_api()
    
    if success:
        show_store_stats()
        
        print(f"\n📅 Test completed at: {datetime.now().isoformat()}")
        print("\n🔗 Store URL: https://7fa66c-ac.myshopify.com")
        print("🔗 Admin URL: https://7fa66c-ac.myshopify.com/admin")
    else:
        print("\n❌ Shopify API test failed")
        print("Please check your configuration and try again")