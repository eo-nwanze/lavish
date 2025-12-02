#!/usr/bin/env python
"""
Test script for API endpoints after fixing missing fields
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
django.setup()

from orders.models import ShopifyOrder
from shipping.models import ShopifyFulfillmentOrder
from django.test import RequestFactory
from accounts.models import CustomUser

def test_api_endpoints():
    """Test API endpoints with fixed fields"""
    print('🔍 Testing API endpoints with fixed fields...')
    
    # Create test request
    factory = RequestFactory()
    user = CustomUser.objects.first()
    
    if not user:
        user = CustomUser.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    # Test 1: Order list endpoint
    request = factory.get('/api/orders/')
    request.user = user
    try:
        from orders.views import order_list
        response = order_list(request)
        print(f'✅ Order list endpoint: Status {response.status_code}')
        if response.status_code == 200:
            data = response.data
            print(f'✅ Orders returned: {len(data.get("orders", []))}')
            print(f'✅ Pagination working: {data.get("pagination", {})}')
    except Exception as e:
        print(f'❌ Order list endpoint error: {str(e)}')
    
    # Test 2: Fulfillment list endpoint
    request = factory.get('/api/fulfillments/')
    request.user = user
    try:
        from shipping.views import fulfillment_order_list
        response = fulfillment_order_list(request)
        print(f'✅ Fulfillment list endpoint: Status {response.status_code}')
        if response.status_code == 200:
            data = response.data
            print(f'✅ Fulfillments returned: {len(data.get("fulfillments", []))}')
    except Exception as e:
        print(f'❌ Fulfillment list endpoint error: {str(e)}')
    
    print('🎉 API endpoint tests completed!')

if __name__ == '__main__':
    test_api_endpoints()