"""
Real-time Orders Sync Service
Based on proven 7fa66cac patterns for live data synchronization
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.conf import settings

from .models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress, OrderSyncLog
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('orders.realtime_sync')


class RealtimeOrderSyncService:
    """
    Real-time order synchronization service
    Provides live data refresh capabilities based on 7fa66cac patterns
    """
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
    
    def sync_all_orders(self, limit: Optional[int] = None) -> Dict:
        """
        Sync all orders from Shopify with real-time data refresh
        """
        logger.info("🔄 Starting real-time order sync...")
        
        try:
            # Fetch orders using enhanced client
            orders_data = self.client.fetch_all_orders(limit=limit)
            
            if not orders_data:
                return {
                    'success': False,
                    'message': 'No orders retrieved from Shopify',
                    'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
                }
            
            # Process orders in batches
            stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0, 'line_items': 0}
            
            with transaction.atomic():
                for order_data in orders_data:
                    try:
                        result = self._sync_single_order(order_data)
                        stats['total'] += 1
                        stats['line_items'] += result['line_items_synced']
                        
                        if result['created']:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error syncing order {order_data.get('id', 'unknown')}: {e}")
                        stats['errors'] += 1
                        continue
            
            logger.info(f"✅ Order sync completed: {stats}")
            
            return {
                'success': True,
                'message': f"Synced {stats['total']} orders successfully",
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Order sync failed: {e}")
            return {
                'success': False,
                'message': f"Order sync failed: {str(e)}",
                'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 1}
            }
    
    def _sync_single_order(self, order_data: Dict) -> Dict:
        """
        Sync a single order with real-time data
        """
        shopify_id = order_data['id']
        
        # Parse timestamps
        created_at = parse_datetime(order_data.get('createdAt'))
        updated_at = parse_datetime(order_data.get('updatedAt'))
        processed_at = parse_datetime(order_data.get('processedAt')) if order_data.get('processedAt') else None
        
        # Extract total price
        total_price_set = order_data.get('totalPriceSet', {})
        shop_money = total_price_set.get('shopMoney', {})
        total_price = shop_money.get('amount', '0.00')
        currency = shop_money.get('currencyCode', 'USD')
        
        # Create or update order
        order, created = ShopifyOrder.objects.update_or_create(
            shopify_id=shopify_id,
            defaults={
                'name': order_data.get('name', ''),
                'email': order_data.get('email', ''),
                'total_price': total_price,
                'currency': currency,
                'financial_status': order_data.get('displayFinancialStatus', 'PENDING'),
                'fulfillment_status': order_data.get('displayFulfillmentStatus', 'UNFULFILLED'),
                'tags': order_data.get('tags', []),
                'note': order_data.get('note', ''),
                'customer_shopify_id': order_data.get('customer', {}).get('id', '') if order_data.get('customer') else '',
                'created_at': created_at,
                'updated_at': updated_at,
                'processed_at': processed_at,
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        # Sync shipping address
        shipping_address = order_data.get('shippingAddress')
        if shipping_address:
            try:
                self._sync_order_address(order, shipping_address, 'shipping')
            except Exception as e:
                logger.warning(f"Failed to sync shipping address for order {shopify_id}: {e}")
        
        # Sync line items
        line_items_synced = 0
        for line_item_edge in order_data.get('lineItems', {}).get('edges', []):
            try:
                self._sync_order_line_item(order, line_item_edge['node'])
                line_items_synced += 1
            except Exception as e:
                logger.warning(f"Failed to sync line item for order {shopify_id}: {e}")
                continue
        
        if created:
            logger.info(f"✅ Created order: {order.name} (${order.total_price} {order.currency}) with {line_items_synced} items")
        else:
            logger.info(f"📝 Updated order: {order.name} (${order.total_price} {order.currency}) with {line_items_synced} items")
        
        return {
            'created': created,
            'order': order,
            'line_items_synced': line_items_synced
        }
    
    def _sync_order_address(self, order: ShopifyOrder, address_data: Dict, address_type: str):
        """
        Sync an order address (shipping or billing)
        """
        address, created = ShopifyOrderAddress.objects.update_or_create(
            order=order,
            address_type=address_type,
            defaults={
                'first_name': address_data.get('firstName', ''),
                'last_name': address_data.get('lastName', ''),
                'address1': address_data.get('address1', ''),
                'address2': address_data.get('address2', ''),
                'city': address_data.get('city', ''),
                'province': address_data.get('province', ''),
                'country': address_data.get('country', ''),
                'zip_code': address_data.get('zip', ''),
                'store_domain': order.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return address, created
    
    def _sync_order_line_item(self, order: ShopifyOrder, line_item_data: Dict):
        """
        Sync an order line item
        """
        variant_data = line_item_data.get('variant', {})
        product_data = line_item_data.get('product', {})
        
        line_item, created = ShopifyOrderLineItem.objects.update_or_create(
            shopify_id=line_item_data['id'],
            defaults={
                'order': order,
                'title': line_item_data.get('title', ''),
                'quantity': line_item_data.get('quantity', 1),
                'variant_shopify_id': variant_data.get('id', ''),
                'variant_title': variant_data.get('title', ''),
                'variant_sku': variant_data.get('sku', ''),
                'variant_price': variant_data.get('price', '0.00'),
                'product_shopify_id': product_data.get('id', ''),
                'product_title': product_data.get('title', ''),
                'store_domain': order.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return line_item, created
    
    def get_sync_statistics(self) -> Dict:
        """
        Get synchronization statistics
        """
        total_orders = ShopifyOrder.objects.count()
        total_line_items = ShopifyOrderLineItem.objects.count()
        total_addresses = ShopifyOrderAddress.objects.count()
        
        # Recent syncs (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_orders = ShopifyOrder.objects.filter(
            last_synced__gte=recent_cutoff
        ).count()
        
        # Status breakdown
        financial_status_counts = {}
        fulfillment_status_counts = {}
        
        for status_choice in ShopifyOrder.FINANCIAL_STATUS_CHOICES:
            status = status_choice[0]
            count = ShopifyOrder.objects.filter(financial_status=status).count()
            if count > 0:
                financial_status_counts[status] = count
        
        for status_choice in ShopifyOrder.FULFILLMENT_STATUS_CHOICES:
            status = status_choice[0]
            count = ShopifyOrder.objects.filter(fulfillment_status=status).count()
            if count > 0:
                fulfillment_status_counts[status] = count
        
        # Revenue calculation
        from django.db.models import Sum
        total_revenue = ShopifyOrder.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        return {
            'total_orders': total_orders,
            'total_line_items': total_line_items,
            'total_addresses': total_addresses,
            'recent_syncs_24h': recent_orders,
            'financial_status_breakdown': financial_status_counts,
            'fulfillment_status_breakdown': fulfillment_status_counts,
            'total_revenue': float(total_revenue),
            'store_domain': self.store_domain,
            'last_check': datetime.now().isoformat()
        }


# Convenience function for easy import
def sync_orders_realtime(limit: Optional[int] = None) -> Dict:
    """
    Convenience function to sync orders in real-time
    """
    service = RealtimeOrderSyncService()
    return service.sync_all_orders(limit=limit)


def get_order_sync_stats() -> Dict:
    """
    Convenience function to get sync statistics
    """
    service = RealtimeOrderSyncService()
    return service.get_sync_statistics()
