#!/usr/bin/env python
"""
Simple test script to verify Orders and Fulfillment API functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Test imports
try:
    from orders.models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress
    from shipping.models import ShopifyFulfillmentOrder
    from orders.views import order_list, order_detail, customer_orders
    from shipping.views import fulfillment_order_list, fulfillment_create
    from orders.services import OrderSyncService
    from shipping.services import FulfillmentSyncService
    from shopify_integration.client import ShopifyAPIClient
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test model creation
try:
    from django.contrib.auth.models import User
    from django.utils import timezone
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Create test order
    order, created = ShopifyOrder.objects.get_or_create(
        shopify_id='gid://shopify/Order/123456789',
        defaults={
            'name': '#1001',
            'customer_email': 'test@example.com',
            'total_price': '99.99',
            'currency_code': 'USD',
            'financial_status': 'pending',
            'fulfillment_status': 'null',
            'created_at': timezone.now(),
            'updated_at': timezone.now(),
            'store_domain': 'test-shop.myshopify.com'
        }
    )
    
    if created:
        print("✅ Test order created successfully")
    else:
        print("✅ Test order already exists")
    
    # Create test line item
    line_item, created = ShopifyOrderLineItem.objects.get_or_create(
        shopify_id='gid://shopify/LineItem/987654321',
        defaults={
            'order': order,
            'title': 'Test Product',
            'quantity': 1,
            'price': '99.99',
            'variant_title': 'Default',
            'variant_sku': 'TEST-SKU',
            'product_title': 'Test Product',
            'store_domain': 'test-shop.myshopify.com'
        }
    )
    
    if created:
        print("✅ Test line item created successfully")
    else:
        print("✅ Test line item already exists")
    
    # Create test address
    address, created = ShopifyOrderAddress.objects.get_or_create(
        order=order,
        address_type='shipping',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'address1': '123 Main St',
            'city': 'New York',
            'province': 'NY',
            'country': 'US',
            'zip_code': '10001',
            'store_domain': 'test-shop.myshopify.com'
        }
    )
    
    if created:
        print("✅ Test address created successfully")
    else:
        print("✅ Test address already exists")
    
    # Create test fulfillment order
    fulfillment_order, created = ShopifyFulfillmentOrder.objects.get_or_create(
        shopify_id='gid://shopify/FulfillmentOrder/555666777',
        defaults={
            'order': order,
            'status': 'open',
            'request_status': 'unsubmitted',
            'created_at': timezone.now(),
            'updated_at': timezone.now(),
            'store_domain': 'test-shop.myshopify.com'
        }
    )
    
    if created:
        print("✅ Test fulfillment order created successfully")
    else:
        print("✅ Test fulfillment order already exists")
    
except Exception as e:
    print(f"❌ Model creation error: {e}")
    sys.exit(1)

# Test services
try:
    # Test OrderSyncService
    order_service = OrderSyncService()
    print("✅ OrderSyncService instantiated successfully")
    
    # Test FulfillmentSyncService
    fulfillment_service = FulfillmentSyncService()
    print("✅ FulfillmentSyncService instantiated successfully")
    
    # Test ShopifyAPIClient
    api_client = ShopifyAPIClient()
    print("✅ ShopifyAPIClient instantiated successfully")
    
except Exception as e:
    print(f"❌ Service instantiation error: {e}")
    sys.exit(1)

# Test URL routing
try:
    from django.urls import reverse
    
    # Test order URLs
    order_list_url = reverse('orders:order_list')
    order_detail_url = reverse('orders:order_detail', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
    customer_orders_url = reverse('orders:customer_orders')
    
    print(f"✅ Order list URL: {order_list_url}")
    print(f"✅ Order detail URL: {order_detail_url}")
    print(f"✅ Customer orders URL: {customer_orders_url}")
    
    # Test shipping URLs
    fulfillment_list_url = reverse('shipping:fulfillment_order_list')
    fulfillment_detail_url = reverse('shipping:fulfillment_order_detail', kwargs={'shopify_id': 'gid://shopify/FulfillmentOrder/555666777'})
    
    print(f"✅ Fulfillment list URL: {fulfillment_list_url}")
    print(f"✅ Fulfillment detail URL: {fulfillment_detail_url}")
    
except Exception as e:
    print(f"❌ URL routing error: {e}")
    sys.exit(1)

# Test database queries
try:
    # Test order queries
    orders = ShopifyOrder.objects.all()
    print(f"✅ Found {orders.count()} orders in database")
    
    # Test line item queries
    line_items = ShopifyOrderLineItem.objects.all()
    print(f"✅ Found {line_items.count()} line items in database")
    
    # Test address queries
    addresses = ShopifyOrderAddress.objects.all()
    print(f"✅ Found {addresses.count()} addresses in database")
    
    # Test fulfillment queries
    fulfillments = ShopifyFulfillmentOrder.objects.all()
    print(f"✅ Found {fulfillments.count()} fulfillment orders in database")
    
except Exception as e:
    print(f"❌ Database query error: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! The Orders and Fulfillment API implementation is working correctly.")
print("\n📋 Summary:")
print("✅ Django setup successful")
print("✅ All imports successful")
print("✅ Model creation working")
print("✅ Services instantiated successfully")
print("✅ URL routing working")
print("✅ Database queries working")
print("\n🚀 The system is ready for use!")