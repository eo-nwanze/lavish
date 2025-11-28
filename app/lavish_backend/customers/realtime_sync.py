"""
Real-time Customer Sync Service
Based on proven 7fa66cac patterns for live data synchronization
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.conf import settings

from .models import ShopifyCustomer, ShopifyCustomerAddress
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('customers.realtime_sync')


class RealtimeCustomerSyncService:
    """
    Real-time customer synchronization service
    Provides live data refresh capabilities based on 7fa66cac patterns
    """
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
    
    def sync_all_customers(self, limit: Optional[int] = None) -> Dict:
        """
        Sync all customers from Shopify with real-time data refresh
        """
        logger.info("🔄 Starting real-time customer sync...")
        
        try:
            # Fetch customers using enhanced client
            customers_data = self.client.fetch_all_customers(limit=limit)
            
            if not customers_data:
                return {
                    'success': False,
                    'message': 'No customers retrieved from Shopify',
                    'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
                }
            
            # Process customers in batches
            stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
            
            with transaction.atomic():
                for customer_data in customers_data:
                    try:
                        result = self._sync_single_customer(customer_data)
                        stats['total'] += 1
                        
                        if result['created']:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error syncing customer {customer_data.get('id', 'unknown')}: {e}")
                        stats['errors'] += 1
                        continue
            
            logger.info(f"✅ Customer sync completed: {stats}")
            
            return {
                'success': True,
                'message': f"Synced {stats['total']} customers successfully",
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Customer sync failed: {e}")
            return {
                'success': False,
                'message': f"Customer sync failed: {str(e)}",
                'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 1}
            }
    
    def _sync_single_customer(self, customer_data: Dict) -> Dict:
        """
        Sync a single customer with real-time data
        """
        shopify_id = customer_data['id']
        
        # Parse timestamps
        created_at = parse_datetime(customer_data.get('createdAt'))
        updated_at = parse_datetime(customer_data.get('updatedAt'))
        
        # Create or update customer
        customer, created = ShopifyCustomer.objects.update_or_create(
            shopify_id=shopify_id,
            defaults={
                'email': customer_data.get('email', ''),
                'first_name': customer_data.get('firstName', ''),
                'last_name': customer_data.get('lastName', ''),
                'phone': customer_data.get('phone', ''),
                'state': customer_data.get('state', 'ENABLED'),
                'verified_email': customer_data.get('verifiedEmail', False),
                'tax_exempt': customer_data.get('taxExempt', False),
                'number_of_orders': customer_data.get('numberOfOrders', 0),
                'tags': customer_data.get('tags', []),
                'created_at': created_at,
                'updated_at': updated_at,
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        # Sync addresses
        addresses_synced = 0
        for address_data in customer_data.get('addresses', []):
            try:
                self._sync_customer_address(customer, address_data)
                addresses_synced += 1
            except Exception as e:
                logger.warning(f"Failed to sync address for customer {shopify_id}: {e}")
                continue
        
        if created:
            logger.info(f"✅ Created customer: {customer.full_name} ({customer.email}) with {addresses_synced} addresses")
        else:
            logger.info(f"📝 Updated customer: {customer.full_name} ({customer.email}) with {addresses_synced} addresses")
        
        return {
            'created': created,
            'customer': customer,
            'addresses_synced': addresses_synced
        }
    
    def _sync_customer_address(self, customer: ShopifyCustomer, address_data: Dict):
        """
        Sync a customer address
        """
        address, created = ShopifyCustomerAddress.objects.update_or_create(
            shopify_id=address_data['id'],
            defaults={
                'customer': customer,
                'first_name': address_data.get('firstName', ''),
                'last_name': address_data.get('lastName', ''),
                'address1': address_data.get('address1', ''),
                'address2': address_data.get('address2', ''),
                'city': address_data.get('city', ''),
                'province': address_data.get('province', ''),
                'country': address_data.get('country', ''),
                'zip_code': address_data.get('zip', ''),
                'phone': address_data.get('phone', ''),
                'province_code': address_data.get('provinceCode', ''),
                'country_code': address_data.get('countryCodeV2', ''),
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return address, created
    
    def sync_customer_by_id(self, shopify_customer_id: str) -> Dict:
        """
        Sync a specific customer by Shopify ID
        """
        logger.info(f"🔄 Syncing customer {shopify_customer_id}...")
        
        # For now, we'll fetch all customers and filter
        # In production, you'd want a single customer query
        customers_data = self.client.fetch_all_customers(limit=100)
        
        for customer_data in customers_data:
            if customer_data['id'] == shopify_customer_id:
                try:
                    result = self._sync_single_customer(customer_data)
                    return {
                        'success': True,
                        'message': f"Customer {shopify_customer_id} synced successfully",
                        'customer': result['customer'],
                        'created': result['created']
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'message': f"Failed to sync customer {shopify_customer_id}: {str(e)}"
                    }
        
        return {
            'success': False,
            'message': f"Customer {shopify_customer_id} not found in Shopify"
        }
    
    def get_sync_statistics(self) -> Dict:
        """
        Get synchronization statistics
        """
        total_customers = ShopifyCustomer.objects.count()
        total_addresses = ShopifyCustomerAddress.objects.count()
        
        # Recent syncs (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_customers = ShopifyCustomer.objects.filter(
            last_synced__gte=recent_cutoff
        ).count()
        
        return {
            'total_customers': total_customers,
            'total_addresses': total_addresses,
            'recent_syncs_24h': recent_customers,
            'store_domain': self.store_domain,
            'last_check': datetime.now().isoformat()
        }
    
    def test_connection(self) -> Dict:
        """
        Test the Shopify API connection
        """
        return self.client.test_connection()


# Convenience function for easy import
def sync_customers_realtime(limit: Optional[int] = None) -> Dict:
    """
    Convenience function to sync customers in real-time
    """
    service = RealtimeCustomerSyncService()
    return service.sync_all_customers(limit=limit)


def get_customer_sync_stats() -> Dict:
    """
    Convenience function to get sync statistics
    """
    service = RealtimeCustomerSyncService()
    return service.get_sync_statistics()
