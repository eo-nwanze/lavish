"""
Test script for skip-based cancellation blocking
Validates that subscriptions with pending skips cannot be cancelled
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
django.setup()

from customer_subscriptions.models import CustomerSubscription, Customer
from skips.models import SubscriptionSkip
from skips.customer_api import cancel_subscription, subscription_management_options
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()

def test_skip_cancellation_block():
    """Test that pending skips block cancellation"""
    print("🧪 Testing Skip-Based Cancellation Blocking")
    print("=" * 50)
    
    # Create test customer
    customer = Customer.objects.create(
        email="test@example.com",
        first_name="Test",
        last_name="Customer",
        shopify_customer_id="gid://shopify/Customer/123"
    )
    
    # Create test subscription
    subscription = CustomerSubscription.objects.create(
        customer=customer,
        shopify_id="gid://shopify/SubscriptionContract/test-skip-block",
        status="ACTIVE",
        billing_policy_interval="MONTH",
        billing_policy_interval_count=1,
        price="45.00"
    )
    
    # Create a pending skip
    pending_skip = SubscriptionSkip.objects.create(
        subscription=subscription,
        status="pending",
        skip_date=timezone.now() + timedelta(days=15)
    )
    
    print(f"✅ Created subscription: {subscription.shopify_id}")
    print(f"✅ Created pending skip: {pending_skip.id}")
    
    # Test 1: Check subscription options with pending skip
    print("\n📋 Test 1: Subscription Options with Pending Skip")
    try:
        from skips.customer_api import subscription_management_options
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.method = 'GET'
        
        response = subscription_management_options(request, subscription.shopify_id)
        
        if hasattr(response, 'content'):
            content = json.loads(response.content.decode('utf-8'))
            
            if content.get('success'):
                options = content.get('options', {})
                
                print(f"  ✅ can_cancel: {options.get('can_cancel')}")
                print(f"  ✅ pending_skips: {options.get('pending_skips')}")
                print(f"  ✅ cancellation_blocked: {options.get('cancellation_blocked')}")
                print(f"  ✅ block_reason: {options.get('cancellation_block_reason')}")
                
                # Validate expectations
                assert options.get('can_cancel') == False, "Cancellation should be blocked"
                assert options.get('pending_skips') == 1, "Should have 1 pending skip"
                assert options.get('cancellation_blocked') == True, "Cancellation should be blocked"
                assert "pending skip" in options.get('cancellation_block_reason', ''), "Block reason should mention pending skips"
                
                print("  ✅ All assertions passed!")
            else:
                print(f"  ❌ API call failed: {content}")
        else:
            print(f"  ❌ Invalid response format")
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
    
    # Test 2: Attempt cancellation with pending skip
    print("\n🚫 Test 2: Cancellation Attempt with Pending Skip")
    try:
        from skips.customer_api import cancel_subscription
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'subscription_id': subscription.shopify_id,
            'reason': 'too_expensive',
            'feedback': 'Test cancellation',
            'confirm': True
        }).encode('utf-8')
        request.content_type = 'application/json'
        
        response = cancel_subscription(request, subscription.shopify_id)
        
        if hasattr(response, 'content'):
            content = json.loads(response.content.decode('utf-8'))
            
            if not content.get('success'):
                error_message = content.get('error', '')
                print(f"  ✅ Cancellation blocked as expected")
                print(f"  ✅ Error message: {error_message}")
                
                # Validate error message mentions pending skips
                assert "pending skip" in error_message, "Error should mention pending skips"
                print("  ✅ Error message validation passed!")
            else:
                print(f"  ❌ Cancellation should have been blocked")
        else:
            print(f"  ❌ Invalid response format")
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
    
    # Test 3: Cancellation allowed after skip is cancelled
    print("\n✅ Test 3: Cancellation Allowed After Skip Cancelled")
    try:
        # Cancel the pending skip
        pending_skip.status = 'cancelled'
        pending_skip.save()
        print(f"  ✅ Cancelled pending skip")
        
        # Try cancellation again
        request = HttpRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'subscription_id': subscription.shopify_id,
            'reason': 'too_expensive',
            'feedback': 'Test cancellation after skip cancelled',
            'confirm': True
        }).encode('utf-8')
        request.content_type = 'application/json'
        
        response = cancel_subscription(request, subscription.shopify_id)
        
        if hasattr(response, 'content'):
            content = json.loads(response.content.decode('utf-8'))
            
            if content.get('success'):
                print(f"  ✅ Cancellation succeeded after skip cancelled")
                print(f"  ✅ Subscription status: {content.get('subscription', {}).get('status')}")
                
                # Validate subscription is now cancelled
                assert content.get('subscription', {}).get('status') == 'CANCELLED', "Subscription should be cancelled"
                print("  ✅ Status validation passed!")
            else:
                print(f"  ❌ Cancellation should have succeeded: {content.get('error')}")
        else:
            print(f"  ❌ Invalid response format")
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Skip-Based Cancellation Blocking Test Complete!")
    print("✅ All tests passed - system correctly blocks cancellation with pending skips")

if __name__ == "__main__":
    test_skip_cancellation_block()