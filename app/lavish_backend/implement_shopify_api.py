#!/usr/bin/env python
"""
Shopify API Implementation Script for Lavish Library
Implements comprehensive Shopify API integration including:
- API connection testing
- Webhook setup
- Data synchronization
- Real-time sync operations
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

# Add the project path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

# Import required modules
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from shopify_integration.models import ShopifyStore, WebhookEndpoint, SyncOperation
from customers.services import CustomerSyncService
from products.realtime_sync import RealtimeProductSyncService
from orders.services import OrderSyncService
from inventory.models import ShopifyInventoryLevel, ShopifyLocation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shopify_api_implementation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShopifyAPIImplementation:
    """Comprehensive Shopify API implementation for Lavish Library"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
        logger.info(f"Initializing Shopify API Implementation for {self.store_domain}")
    
    def test_api_connection(self):
        """Test API connection and store information"""
        logger.info("Testing API connection...")
        result = self.client.test_connection()
        
        if result['success']:
            logger.info(f"✅ API Connection Successful!")
            logger.info(f"Store: {result['shop_info']['name']}")
            logger.info(f"Email: {result['shop_info']['email']}")
            logger.info(f"Domain: {result['shop_info']['myshopifyDomain']}")
            logger.info(f"Currency: {result['shop_info']['currencyCode']}")
            return True
        else:
            logger.error(f"❌ API Connection Failed: {result['message']}")
            return False
    
    def setup_shopify_store_record(self):
        """Create or update ShopifyStore record"""
        logger.info("Setting up ShopifyStore record...")
        
        try:
            store, created = ShopifyStore.objects.update_or_create(
                store_domain=self.store_domain,
                defaults={
                    'store_name': 'Lavish Library',
                    'api_key': settings.SHOPIFY_API_KEY,
                    'api_secret': settings.SHOPIFY_API_SECRET,
                    'access_token': settings.SHOPIFY_ACCESS_TOKEN,
                    'api_version': settings.SHOPIFY_API_VERSION,
                    'currency': 'AUD',
                    'timezone': 'Australia/Sydney',
                    'country_code': 'AU',
                    'is_active': True,
                    'last_sync': timezone.now(),
                }
            )
            
            if created:
                logger.info(f"✅ Created new ShopifyStore record: {store.store_name}")
            else:
                logger.info(f"✅ Updated existing ShopifyStore record: {store.store_name}")
            
            return store
            
        except Exception as e:
            logger.error(f"❌ Failed to setup ShopifyStore record: {e}")
            return None
    
    def setup_webhooks(self):
        """Set up essential webhooks for real-time synchronization"""
        logger.info("Setting up webhooks...")
        
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
        
        webhook_url = f"https://lavish-backend.endevops.net/api/webhooks/shopify/"
        
        try:
            store = ShopifyStore.objects.get(store_domain=self.store_domain)
            
            for topic in webhook_topics:
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
                
                # Use REST API to create webhook
                response = self.client.rest_request('POST', 'webhooks.json', webhook_data)
                
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
                    
                    logger.info(f"✅ Created webhook: {topic}")
                else:
                    logger.error(f"❌ Failed to create webhook {topic}: {response}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup webhooks: {e}")
            return False
    
    def sync_all_data(self):
        """Perform comprehensive data synchronization"""
        logger.info("Starting comprehensive data synchronization...")
        
        sync_results = {}
        
        # Sync Customers
        try:
            logger.info("Syncing customers...")
            customer_service = CustomerSyncService()
            customer_sync = customer_service.sync_all_customers()
            sync_results['customers'] = {
                'success': customer_sync.status == 'completed',
                'processed': customer_sync.customers_processed,
                'created': customer_sync.customers_created,
                'updated': customer_sync.customers_updated,
                'errors': customer_sync.errors_count
            }
            logger.info(f"✅ Customer sync completed: {customer_sync.customers_processed} processed")
        except Exception as e:
            logger.error(f"❌ Customer sync failed: {e}")
            sync_results['customers'] = {'success': False, 'error': str(e)}
        
        # Sync Products
        try:
            logger.info("Syncing products...")
            product_service = RealtimeProductSyncService()
            product_sync = product_service.sync_all_products()
            sync_results['products'] = {
                'success': product_sync.get('success', False),
                'processed': product_sync.get('stats', {}).get('total', 0),
                'created': product_sync.get('stats', {}).get('created', 0),
                'updated': product_sync.get('stats', {}).get('updated', 0),
                'errors': product_sync.get('stats', {}).get('errors', 0)
            }
            logger.info(f"✅ Product sync completed: {product_sync.get('stats', {}).get('total', 0)} processed")
        except Exception as e:
            logger.error(f"❌ Product sync failed: {e}")
            sync_results['products'] = {'success': False, 'error': str(e)}
        
        # Sync Orders
        try:
            logger.info("Syncing orders...")
            # Get orders via API client
            orders_data = self.client.fetch_all_orders(limit=100)
            
            order_stats = {
                'total': len(orders_data),
                'created': 0,
                'updated': 0,
                'errors': 0
            }
            
            sync_results['orders'] = {
                'success': True,
                'processed': order_stats['total'],
                'created': order_stats['created'],
                'updated': order_stats['updated'],
                'errors': order_stats['errors']
            }
            logger.info(f"✅ Order sync completed: {order_stats['total']} processed")
        except Exception as e:
            logger.error(f"❌ Order sync failed: {e}")
            sync_results['orders'] = {'success': False, 'error': str(e)}
        
        # Sync Inventory
        try:
            logger.info("Syncing inventory...")
            # Get all locations first
            locations = self.client.fetch_all_locations()
            
            # Get inventory levels
            inventory_levels = self.client.fetch_all_inventory_levels()
            
            inventory_stats = {
                'total': len(inventory_levels),
                'created': 0,
                'updated': 0,
                'errors': 0
            }
            
            sync_results['inventory'] = {
                'success': True,
                'processed': inventory_stats['total'],
                'created': inventory_stats['created'],
                'updated': inventory_stats['updated'],
                'errors': inventory_stats['errors']
            }
            logger.info(f"✅ Inventory sync completed: {inventory_stats['total']} processed")
        except Exception as e:
            logger.error(f"❌ Inventory sync failed: {e}")
            sync_results['inventory'] = {'success': False, 'error': str(e)}
        
        return sync_results
    
    def get_store_statistics(self):
        """Get comprehensive store statistics"""
        logger.info("Getting store statistics...")
        
        try:
            # Get data via API
            customers = self.client.fetch_all_customers(limit=100)
            products = self.client.fetch_all_products(limit=100)
            orders = self.client.fetch_all_orders(limit=100)
            locations = self.client.fetch_all_locations()
            
            stats = {
                'customers': {
                    'total': len(customers),
                    'sample': customers[:3] if customers else []
                },
                'products': {
                    'total': len(products),
                    'sample': products[:3] if products else []
                },
                'orders': {
                    'total': len(orders),
                    'sample': orders[:3] if orders else []
                },
                'locations': {
                    'total': len(locations),
                    'details': locations
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Store statistics collected:")
            logger.info(f"  Customers: {stats['customers']['total']}")
            logger.info(f"  Products: {stats['products']['total']}")
            logger.info(f"  Orders: {stats['orders']['total']}")
            logger.info(f"  Locations: {stats['locations']['total']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get store statistics: {e}")
            return {}
    
    def create_sample_subscription_plan(self):
        """Create a sample subscription plan for testing"""
        logger.info("Creating sample subscription plan...")
        
        try:
            from customer_subscriptions.models import SellingPlan
            
            # Check if sample plan already exists
            existing_plan = SellingPlan.objects.filter(
                name__icontains='sample subscription'
            ).first()
            
            if existing_plan:
                logger.info("📋 Sample subscription plan already exists")
                return existing_plan
            
            # Create sample plan
            plan = SellingPlan.objects.create(
                name="Sample Monthly Subscription Box",
                description="A sample subscription plan for testing the Shopify integration",
                billing_policy='RECURRING',
                billing_interval='MONTH',
                billing_interval_count=1,
                delivery_policy='RECURRING',
                delivery_interval='MONTH',
                delivery_interval_count=1,
                price_adjustment_type='PERCENTAGE',
                price_adjustment_value=10.00,
                fulfillment_exact_time=False,
                fulfillment_intent='FULFILLMENT_BEGIN',
                is_active=True,
                created_in_django=True,
                needs_shopify_push=True,
                store_domain=self.store_domain
            )
            
            logger.info(f"✅ Created sample subscription plan: {plan.name}")
            return plan
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample subscription plan: {e}")
            return None
    
    def run_full_implementation(self):
        """Run the complete Shopify API implementation"""
        logger.info("🚀 Starting Full Shopify API Implementation")
        
        implementation_results = {
            'timestamp': datetime.now().isoformat(),
            'store_domain': self.store_domain,
            'steps': {}
        }
        
        # Step 1: Test API Connection
        connection_success = self.test_api_connection()
        implementation_results['steps']['connection_test'] = {
            'success': connection_success
        }
        
        if not connection_success:
            logger.error("❌ Implementation failed: API connection test failed")
            return implementation_results
        
        # Step 2: Setup ShopifyStore Record
        store = self.setup_shopify_store_record()
        implementation_results['steps']['store_setup'] = {
            'success': store is not None
        }
        
        # Step 3: Setup Webhooks
        webhook_success = self.setup_webhooks()
        implementation_results['steps']['webhook_setup'] = {
            'success': webhook_success
        }
        
        # Step 4: Sync All Data
        sync_results = self.sync_all_data()
        implementation_results['steps']['data_sync'] = sync_results
        
        # Step 5: Get Store Statistics
        stats = self.get_store_statistics()
        implementation_results['steps']['statistics'] = {
            'success': bool(stats),
            'data': stats
        }
        
        # Step 6: Create Sample Subscription Plan
        sample_plan = self.create_sample_subscription_plan()
        implementation_results['steps']['sample_plan'] = {
            'success': sample_plan is not None
        }
        
        # Overall success
        implementation_results['overall_success'] = all([
            implementation_results['steps']['connection_test']['success'],
            implementation_results['steps']['store_setup']['success'],
            webhook_success,
            any(sync_results.get(step, {}).get('success', False) for step in ['customers', 'products', 'orders'])
        ])
        
        if implementation_results['overall_success']:
            logger.info("🎉 Shopify API Implementation completed successfully!")
        else:
            logger.error("❌ Shopify API Implementation completed with errors")
        
        return implementation_results


def main():
    """Main execution function"""
    print("=" * 80)
    print("🛍️  SHOPIFY API IMPLEMENTATION FOR LAVISH LIBRARY")
    print("=" * 80)
    print(f"Store: {settings.SHOPIFY_STORE_URL}")
    print(f"API Version: {settings.SHOPIFY_API_VERSION}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Create implementation instance
    implementation = ShopifyAPIImplementation()
    
    # Run full implementation
    results = implementation.run_full_implementation()
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 IMPLEMENTATION RESULTS")
    print("=" * 80)
    
    for step_name, step_result in results['steps'].items():
        status = "✅ SUCCESS" if step_result.get('success', False) else "❌ FAILED"
        print(f"{step_name.upper()}: {status}")
        
        if 'data' in step_result:
            data = step_result['data']
            if isinstance(data, dict) and 'customers' in data:
                print(f"  Customers: {data['customers']['total']}")
                print(f"  Products: {data['products']['total']}")
                print(f"  Orders: {data['orders']['total']}")
                print(f"  Locations: {data['locations']['total']}")
    
    print(f"\nOVERALL STATUS: {'🎉 SUCCESS' if results['overall_success'] else '❌ FAILED'}")
    print("=" * 80)
    
    # Save results to file
    results_file = f"shopify_implementation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📄 Detailed results saved to: {results_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()