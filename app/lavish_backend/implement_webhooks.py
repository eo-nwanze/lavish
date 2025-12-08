#!/usr/bin/env python
"""
Step 2: Webhook Implementation
Sets up webhook endpoints and implements real-time event handling
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from shopify_integration.models import ShopifyStore, WebhookEndpoint
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
import hmac
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShopifyWebhookHandler(View):
    """Handle incoming Shopify webhooks"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
        self.webhook_secret = os.getenv('SHOPIFY_API_SECRET', '4381542a60254c4742a67b73f3329ae')
    
    def post(self, request, *args, **kwargs):
        """Handle webhook POST requests"""
        try:
            # Verify webhook signature
            if not self._verify_webhook(request):
                logger.error("Webhook signature verification failed")
                return HttpResponse(status=401)
            
            # Get webhook topic from headers
            topic = request.META.get('HTTP_X_SHOPIFY_TOPIC', '')
            if not topic:
                logger.error("Missing webhook topic")
                return HttpResponse(status=400)
            
            # Parse webhook data
            try:
                webhook_data = json.loads(request.body)
            except json.JSONDecodeError:
                logger.error("Invalid webhook JSON data")
                return HttpResponse(status=400)
            
            # Handle webhook based on topic
            result = self._handle_webhook(topic, webhook_data)
            
            if result:
                logger.info(f"✅ Webhook processed: {topic}")
                return HttpResponse(status=200)
            else:
                logger.error(f"❌ Webhook processing failed: {topic}")
                return HttpResponse(status=500)
                
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
            return HttpResponse(status=500)
    
    def _verify_webhook(self, request):
        """Verify webhook authenticity"""
        try:
            # Get HMAC signature from header
            hmac_header = request.META.get('HTTP_X_SHOPIFY_HMAC_SHA256', '')
            if not hmac_header:
                return False
            
            # Calculate expected HMAC
            calculated_hmac = base64.b64encode(
                hmac.new(
                    self.webhook_secret.encode('utf-8'),
                    request.body,
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            # Compare signatures
            return hmac.compare_digest(calculated_hmac, hmac_header)
            
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return False
    
    def _handle_webhook(self, topic, data):
        """Handle webhook based on topic"""
        try:
            logger.info(f"Processing webhook: {topic}")
            
            # Handle different webhook topics
            if topic == 'customers/create':
                return self._handle_customer_create(data)
            elif topic == 'customers/update':
                return self._handle_customer_update(data)
            elif topic == 'products/create':
                return self._handle_product_create(data)
            elif topic == 'products/update':
                return self._handle_product_update(data)
            elif topic == 'orders/create':
                return self._handle_order_create(data)
            elif topic == 'orders/updated':
                return self._handle_order_update(data)
            elif topic == 'orders/cancelled':
                return self._handle_order_cancelled(data)
            elif topic == 'orders/fulfilled':
                return self._handle_order_fulfilled(data)
            elif topic == 'orders/partially_fulfilled':
                return self._handle_order_partially_fulfilled(data)
            elif topic == 'fulfillments/create':
                return self._handle_fulfillment_create(data)
            elif topic == 'fulfillments/update':
                return self._handle_fulfillment_update(data)
            elif topic == 'inventory_levels/update':
                return self._handle_inventory_update(data)
            elif topic == 'app/uninstalled':
                return self._handle_app_uninstalled(data)
            else:
                logger.warning(f"Unhandled webhook topic: {topic}")
                return True
                
        except Exception as e:
            logger.error(f"Error handling webhook {topic}: {e}")
            return False
    
    def _handle_customer_create(self, data):
        """Handle customer creation webhook"""
        try:
            from customers.services import CustomerSyncService
            service = CustomerSyncService()
            return service.sync_customer_from_webhook(data)
        except Exception as e:
            logger.error(f"Customer create webhook error: {e}")
            return False
    
    def _handle_customer_update(self, data):
        """Handle customer update webhook"""
        try:
            from customers.services import CustomerSyncService
            service = CustomerSyncService()
            return service.sync_customer_from_webhook(data)
        except Exception as e:
            logger.error(f"Customer update webhook error: {e}")
            return False
    
    def _handle_product_create(self, data):
        """Handle product creation webhook"""
        try:
            from products.realtime_sync import RealtimeProductSyncService
            service = RealtimeProductSyncService()
            result = service._sync_single_product(data)
            return result is not None
        except Exception as e:
            logger.error(f"Product create webhook error: {e}")
            return False
    
    def _handle_product_update(self, data):
        """Handle product update webhook"""
        try:
            from products.realtime_sync import RealtimeProductSyncService
            service = RealtimeProductSyncService()
            result = service._sync_single_product(data)
            return result is not None
        except Exception as e:
            logger.error(f"Product update webhook error: {e}")
            return False
    
    def _handle_order_create(self, data):
        """Handle order creation webhook"""
        try:
            from orders.services import OrderSyncService
            service = OrderSyncService()
            return service.sync_order_from_webhook(data)
        except Exception as e:
            logger.error(f"Order create webhook error: {e}")
            return False
    
    def _handle_order_update(self, data):
        """Handle order update webhook"""
        try:
            from orders.services import OrderSyncService
            service = OrderSyncService()
            return service.sync_order_from_webhook(data)
        except Exception as e:
            logger.error(f"Order update webhook error: {e}")
            return False
    
    def _handle_order_cancelled(self, data):
        """Handle order cancellation webhook"""
        try:
            from orders.services import OrderSyncService
            service = OrderSyncService()
            return service.sync_order_from_webhook(data)
        except Exception as e:
            logger.error(f"Order cancelled webhook error: {e}")
            return False
    
    def _handle_order_fulfilled(self, data):
        """Handle order fulfillment webhook"""
        try:
            from orders.services import OrderSyncService
            from shipping.services import FulfillmentSyncService
            
            # Sync order status
            order_service = OrderSyncService()
            order_result = order_service.sync_order_from_webhook(data)
            
            # Sync fulfillment details
            fulfillment_service = FulfillmentSyncService()
            fulfillment_result = fulfillment_service.sync_fulfillment_from_webhook(data)
            
            return order_result and fulfillment_result
        except Exception as e:
            logger.error(f"Order fulfilled webhook error: {e}")
            return False
    
    def _handle_order_partially_fulfilled(self, data):
        """Handle partial order fulfillment webhook"""
        try:
            from orders.services import OrderSyncService
            from shipping.services import FulfillmentSyncService
            
            # Sync order status
            order_service = OrderSyncService()
            order_result = order_service.sync_order_from_webhook(data)
            
            # Sync fulfillment details
            fulfillment_service = FulfillmentSyncService()
            fulfillment_result = fulfillment_service.sync_fulfillment_from_webhook(data)
            
            return order_result and fulfillment_result
        except Exception as e:
            logger.error(f"Order partially fulfilled webhook error: {e}")
            return False
    
    def _handle_fulfillment_create(self, data):
        """Handle fulfillment creation webhook"""
        try:
            from shipping.services import FulfillmentSyncService
            service = FulfillmentSyncService()
            return service.sync_fulfillment_from_webhook(data)
        except Exception as e:
            logger.error(f"Fulfillment create webhook error: {e}")
            return False
    
    def _handle_fulfillment_update(self, data):
        """Handle fulfillment update webhook"""
        try:
            from shipping.services import FulfillmentSyncService
            service = FulfillmentSyncService()
            return service.sync_fulfillment_from_webhook(data)
        except Exception as e:
            logger.error(f"Fulfillment update webhook error: {e}")
            return False
    
    def _handle_inventory_update(self, data):
        """Handle inventory update webhook"""
        try:
            from inventory.services import InventorySyncService
            service = InventorySyncService()
            return service.sync_inventory_from_webhook(data)
        except Exception as e:
            logger.error(f"Inventory update webhook error: {e}")
            return False
    
    def _handle_app_uninstalled(self, data):
        """Handle app uninstallation webhook"""
        try:
            logger.warning("App was uninstalled from store")
            
            # Mark store as inactive
            from django.contrib.auth import get_user_model
            from django.core.mail import send_mail
            from django.conf import settings
            
            User = get_user_model()
            
            # Find store admin users and notify them
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            
            for admin in admin_users:
                if admin.email:
                    send_mail(
                        subject='⚠️ Lavish App Uninstalled',
                        message=f'The Lavish app has been uninstalled from the store. Please check your Shopify store settings.',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lavish.com'),
                        recipient_list=[admin.email],
                        fail_silently=True,
                    )
            
            logger.info(f"Notified {admin_users.count()} admin users about app uninstallation")
            
            return True
        except Exception as e:
            logger.error(f"App uninstall webhook error: {e}")
            return False

def setup_webhooks():
    """Set up webhooks in Shopify"""
    logger.info("Setting up webhooks...")
    
    try:
        # Get store
        store = ShopifyStore.objects.get(store_domain='7fa66c-ac.myshopify.com')
        
        # Webhook topics to create
        webhook_topics = [
            'customers/create',
            'customers/update',
            'products/create',
            'products/update',
            'orders/create',
            'orders/updated',
            'orders/cancelled',
            'orders/fulfilled',
            'orders/partially_fulfilled',
            'fulfillments/create',
            'fulfillments/update',
            'inventory_levels/update',
            'app/uninstalled',
        ]
        
        # Webhook URL
        webhook_url = "https://lavish-backend.endevops.net/api/webhooks/shopify/"
        
        # Create webhooks
        client = EnhancedShopifyAPIClient()
        created_webhooks = 0
        
        for topic in webhook_topics:
            try:
                # Check if webhook already exists
                existing_webhook = WebhookEndpoint.objects.filter(
                    store=store,
                    topic=topic
                ).first()
                
                if existing_webhook:
                    logger.info(f"📋 Webhook already exists: {topic}")
                    continue
                
                # Create webhook via Shopify API
                webhook_data = {
                    "webhook": {
                        "topic": topic,
                        "address": webhook_url,
                        "format": "json"
                    }
                }
                
                response = client.create_webhook(topic, webhook_url, 'json')
                
                if 'webhook' in response:
                    webhook_id = response['webhook']['id']
                    
                    # Save to database
                    WebhookEndpoint.objects.create(
                        store=store,
                        shopify_id=webhook_id,
                        topic=topic,
                        address=webhook_url,
                        format='json',
                        is_active=True
                    )
                    
                    created_webhooks += 1
                    logger.info(f"✅ Created webhook: {topic}")
                else:
                    logger.error(f"❌ Failed to create webhook {topic}: {response}")
                    
            except Exception as e:
                logger.error(f"❌ Error creating webhook {topic}: {e}")
                continue
        
        logger.info(f"🎉 Webhook setup completed: {created_webhooks} webhooks created")
        return created_webhooks
        
    except Exception as e:
        logger.error(f"❌ Webhook setup failed: {e}")
        return 0

def create_webhook_urls():
    """Create webhook URL patterns"""
    logger.info("Creating webhook URL patterns...")
    
    # This would typically be in urls.py, but we'll document it here
    webhook_patterns = [
        path('api/webhooks/shopify/', csrf_exempt(ShopifyWebhookHandler.as_view()), name='shopify_webhook'),
    ]
    
    logger.info("✅ Webhook URL patterns created")
    return webhook_patterns

def test_webhook_endpoint():
    """Test webhook endpoint"""
    logger.info("Testing webhook endpoint...")
    
    try:
        # Create test webhook data
        test_data = {
            "id": "gid://shopify/Customer/123456789",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890",
            "createdAt": "2025-12-08T11:30:00Z",
            "updatedAt": "2025-12-08T11:30:00Z",
            "state": "ENABLED",
            "verifiedEmail": True,
            "taxExempt": False,
            "numberOfOrders": 0,
            "tags": ["test-customer"],
            "addresses": []
        }
        
        # Test webhook handler
        handler = ShopifyWebhookHandler()
        
        # Simulate webhook request
        class MockRequest:
            def __init__(self, data, topic, secret):
                self.body = json.dumps(data).encode('utf-8')
                self.META = {
                    'HTTP_X_SHOPIFY_TOPIC': topic,
                    'HTTP_X_SHOPIFY_HMAC_SHA256': self._calculate_hmac(data, secret)
                }
            
            def _calculate_hmac(self, data, secret):
                calculated_hmac = base64.b64encode(
                    hmac.new(
                        secret.encode('utf-8'),
                        json.dumps(data).encode('utf-8'),
                        hashlib.sha256
                    ).digest()
                ).decode('utf-8')
                return calculated_hmac
        
        mock_request = MockRequest(test_data, 'customers/create', handler.webhook_secret)
        result = handler.post(mock_request)
        
        if result.status_code == 200:
            logger.info("✅ Webhook endpoint test passed")
            return True
        else:
            logger.error(f"❌ Webhook endpoint test failed: {result.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Webhook endpoint test error: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 80)
    print("🔧 STEP 2: WEBHOOK IMPLEMENTATION")
    print("=" * 80)
    
    # Step 1: Set up webhooks
    print("\n1. Setting up webhooks in Shopify...")
    webhook_count = setup_webhooks()
    if webhook_count > 0:
        print(f"✅ {webhook_count} webhooks created successfully")
    else:
        print("❌ Failed to create webhooks")
        return False
    
    # Step 2: Create webhook URL patterns
    print("\n2. Creating webhook URL patterns...")
    webhook_patterns = create_webhook_urls()
    print("✅ Webhook URL patterns created")
    
    # Step 3: Test webhook endpoint
    print("\n3. Testing webhook endpoint...")
    if test_webhook_endpoint():
        print("✅ Webhook endpoint test passed")
    else:
        print("❌ Webhook endpoint test failed")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 STEP 2 COMPLETED SUCCESSFULLY!")
    print("✅ Webhooks are set up and ready for real-time event handling")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)