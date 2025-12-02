"""
Order Sync Service
Handles real-time synchronization of order data from Shopify webhooks
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.conf import settings

from .models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress, OrderSyncLog
from shopify_integration.client import ShopifyAPIClient

logger = logging.getLogger('orders.services')


class OrderSyncService:
    """
    Service for synchronizing order data from Shopify webhooks
    """
    
    def __init__(self):
        self.client = ShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
    
    def sync_order_from_webhook(self, webhook_data: Dict) -> bool:
        """
        Sync order data from webhook payload
        
        Args:
            webhook_data: Shopify webhook payload for order events
            
        Returns:
            bool: True if sync was successful
        """
        try:
            logger.info(f"Processing order webhook: {webhook_data.get('name', webhook_data.get('id', 'unknown'))}")
            
            # Extract order data
            order_id = webhook_data.get('id')
            
            if not order_id:
                logger.error("Missing order ID in webhook data")
                return False
            
            # Parse timestamps
            created_at = parse_datetime(webhook_data.get('created_at'))
            updated_at = parse_datetime(webhook_data.get('updated_at'))
            processed_at = parse_datetime(webhook_data.get('processed_at')) if webhook_data.get('processed_at') else None
            cancelled_at = parse_datetime(webhook_data.get('cancelled_at')) if webhook_data.get('cancelled_at') else None
            
            # Extract customer information
            customer = webhook_data.get('customer', {})
            customer_shopify_id = customer.get('id', '') if customer else ''
            
            # Extract total price
            total_price_set = webhook_data.get('total_price_set', {})
            shop_money = total_price_set.get('shop_money', {})
            total_price = shop_money.get('amount', '0.00')
            currency = shop_money.get('currency_code', 'USD')
            
            # Create or update order
            with transaction.atomic():
                order, created = ShopifyOrder.objects.update_or_create(
                    shopify_id=order_id,
                    defaults={
                        'name': webhook_data.get('name', ''),
                        'customer_email': webhook_data.get('email', ''),
                        'customer_phone': webhook_data.get('phone', ''),
                        'customer_shopify_id': customer_shopify_id,
                        'total_price': total_price,
                        'currency_code': currency,
                        'financial_status': webhook_data.get('financial_status', 'pending'),
                        'fulfillment_status': webhook_data.get('fulfillment_status', 'null'),
                        'subtotal_price': webhook_data.get('subtotal_price', '0.00'),
                        'total_tax': webhook_data.get('total_tax', '0.00'),
                        'total_shipping_price': webhook_data.get('total_shipping_price', '0.00'),
                        'tags': webhook_data.get('tags', '').split(', ') if webhook_data.get('tags') else [],
                        'note': webhook_data.get('note', ''),
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'processed_at': processed_at,
                        'cancelled_at': cancelled_at,
                        'store_domain': self.store_domain,
                        'last_synced': datetime.now(),
                    }
                )
                
                # Sync addresses
                shipping_address = webhook_data.get('shipping_address')
                if shipping_address:
                    try:
                        self._sync_order_address(order, shipping_address, 'shipping')
                    except Exception as e:
                        logger.warning(f"Failed to sync shipping address for order {order_id}: {e}")
                
                billing_address = webhook_data.get('billing_address')
                if billing_address:
                    try:
                        self._sync_order_address(order, billing_address, 'billing')
                    except Exception as e:
                        logger.warning(f"Failed to sync billing address for order {order_id}: {e}")
                
                # Sync line items
                line_items = webhook_data.get('line_items', [])
                for line_item in line_items:
                    try:
                        self._sync_order_line_item(order, line_item)
                    except Exception as e:
                        logger.warning(f"Failed to sync line item for order {order_id}: {e}")
                        continue
                
                if created:
                    logger.info(f"✅ Created order: {order.name} (${order.total_price} {order.currency_code})")
                else:
                    logger.info(f"📝 Updated order: {order.name} (${order.total_price} {order.currency_code})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync order from webhook: {str(e)}", exc_info=True)
            return False
    
    def _sync_order_address(self, order: ShopifyOrder, address_data: Dict, address_type: str):
        """
        Sync an order address (shipping or billing)
        """
        address, created = ShopifyOrderAddress.objects.update_or_create(
            order=order,
            address_type=address_type,
            defaults={
                'first_name': address_data.get('first_name', ''),
                'last_name': address_data.get('last_name', ''),
                'company': address_data.get('company', ''),
                'address1': address_data.get('address1', ''),
                'address2': address_data.get('address2', ''),
                'city': address_data.get('city', ''),
                'province': address_data.get('province', ''),
                'country': address_data.get('country', ''),
                'zip_code': address_data.get('zip', ''),
                'phone': address_data.get('phone', ''),
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
                'price': line_item_data.get('price', '0.00'),
                'variant_shopify_id': variant_data.get('id', '') if variant_data else '',
                'variant_title': variant_data.get('title', '') if variant_data else '',
                'variant_sku': variant_data.get('sku', '') if variant_data else '',
                'product_shopify_id': product_data.get('id', '') if product_data else '',
                'product_title': product_data.get('title', '') if product_data else '',
                'store_domain': order.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return line_item, created
    
    def sync_order_from_shopify(self, order_shopify_id: str) -> Dict:
        """
        Sync a single order from Shopify API
        
        Args:
            order_shopify_id: Shopify order ID
            
        Returns:
            Dict: Sync result
        """
        try:
            logger.info(f"Syncing order from Shopify: {order_shopify_id}")
            
            # Get order from Shopify
            order_data = self.client.get_order(order_shopify_id)
            
            if not order_data:
                return {
                    'success': False,
                    'message': f'Order {order_shopify_id} not found in Shopify'
                }
            
            # Sync order using webhook logic
            success = self.sync_order_from_webhook(order_data)
            
            if success:
                order = ShopifyOrder.objects.get(shopify_id=order_shopify_id)
                return {
                    'success': True,
                    'message': f'Successfully synced order {order.name}',
                    'order': {
                        'id': order.id,
                        'shopify_id': order.shopify_id,
                        'name': order.name,
                        'total_price': str(order.total_price),
                        'currency_code': order.currency_code,
                        'financial_status': order.financial_status,
                        'fulfillment_status': order.fulfillment_status,
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to sync order {order_shopify_id}'
                }
                
        except Exception as e:
            logger.error(f"❌ Order sync from Shopify failed: {e}")
            return {
                'success': False,
                'message': f'Order sync failed: {str(e)}'
            }
    
    def get_order_sync_statistics(self) -> Dict:
        """
        Get order synchronization statistics
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
def sync_order_from_webhook(webhook_data: Dict) -> bool:
    """
    Convenience function to sync order from webhook
    """
    service = OrderSyncService()
    return service.sync_order_from_webhook(webhook_data)


def get_order_sync_stats() -> Dict:
    """
    Convenience function to get order sync statistics
    """
    service = OrderSyncService()
    return service.get_order_sync_statistics()