"""
Fulfillment Sync Service
Handles real-time synchronization of fulfillment data from Shopify webhooks
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.conf import settings

from .models import ShopifyFulfillmentOrder
from orders.models import ShopifyOrder
from shopify_integration.client import ShopifyAPIClient

logger = logging.getLogger('shipping.services')


class FulfillmentSyncService:
    """
    Service for synchronizing fulfillment data from Shopify webhooks
    """
    
    def __init__(self):
        self.client = ShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
    
    def sync_fulfillment_from_webhook(self, webhook_data: Dict) -> bool:
        """
        Sync fulfillment data from webhook payload
        
        Args:
            webhook_data: Shopify webhook payload for fulfillment events
            
        Returns:
            bool: True if sync was successful
        """
        try:
            logger.info(f"Processing fulfillment webhook: {webhook_data.get('id', 'unknown')}")
            
            # Extract fulfillment data
            fulfillment_id = webhook_data.get('id')
            order_id = webhook_data.get('order_id')
            
            if not fulfillment_id or not order_id:
                logger.error("Missing fulfillment_id or order_id in webhook data")
                return False
            
            # Get related order
            try:
                order = ShopifyOrder.objects.get(shopify_id=order_id)
            except ShopifyOrder.DoesNotExist:
                logger.error(f"Order {order_id} not found for fulfillment {fulfillment_id}")
                return False
            
            # Parse timestamps
            created_at = parse_datetime(webhook_data.get('created_at'))
            updated_at = parse_datetime(webhook_data.get('updated_at'))
            
            # Extract tracking information
            tracking_info = webhook_data.get('tracking_info', {})
            tracking_company = tracking_info.get('company', '')
            tracking_numbers = tracking_info.get('numbers', [])
            tracking_urls = tracking_info.get('urls', [])
            
            # Create or update fulfillment order
            with transaction.atomic():
                fulfillment_order, created = ShopifyFulfillmentOrder.objects.update_or_create(
                    shopify_id=fulfillment_id,
                    defaults={
                        'order': order,
                        'status': webhook_data.get('status', 'open'),
                        'request_status': webhook_data.get('request_status', 'unsubmitted'),
                        'fulfill_at': parse_datetime(webhook_data.get('fulfill_at')) if webhook_data.get('fulfill_at') else None,
                        'fulfill_by': parse_datetime(webhook_data.get('fulfill_by')) if webhook_data.get('fulfill_by') else None,
                        'international_duties': webhook_data.get('international_duties'),
                        'delivery_method': webhook_data.get('delivery_method'),
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'store_domain': self.store_domain,
                    }
                )
                
                # Update order fulfillment status
                if webhook_data.get('status') == 'success':
                    order.fulfillment_status = 'fulfilled'
                elif webhook_data.get('status') == 'cancelled':
                    order.fulfillment_status = 'null'  # Reset to unfulfilled
                elif webhook_data.get('status') == 'partial':
                    order.fulfillment_status = 'partial'
                
                order.save()
                
                # Log tracking information
                if tracking_numbers:
                    logger.info(f"Fulfillment {fulfillment_id} tracking: {tracking_company} - {tracking_numbers}")
                
                if created:
                    logger.info(f"✅ Created fulfillment order: {fulfillment_id}")
                else:
                    logger.info(f"📝 Updated fulfillment order: {fulfillment_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync fulfillment from webhook: {str(e)}", exc_info=True)
            return False
    
    def sync_fulfillment_orders_for_order(self, order_shopify_id: str) -> Dict:
        """
        Sync all fulfillment orders for a specific order
        
        Args:
            order_shopify_id: Shopify order ID
            
        Returns:
            Dict: Sync results with statistics
        """
        try:
            logger.info(f"Syncing fulfillment orders for order: {order_shopify_id}")
            
            # Get order
            order = ShopifyOrder.objects.get(shopify_id=order_shopify_id)
            
            # Fetch fulfillment orders from Shopify
            fulfillment_orders_data = self.client.get_fulfillment_orders(order_shopify_id)
            
            if not fulfillment_orders_data:
                return {
                    'success': False,
                    'message': 'No fulfillment orders found',
                    'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
                }
            
            # Process fulfillment orders
            stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
            
            with transaction.atomic():
                for fulfillment_data in fulfillment_orders_data:
                    try:
                        result = self._sync_single_fulfillment_order(order, fulfillment_data)
                        stats['total'] += 1
                        
                        if result['created']:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error syncing fulfillment order {fulfillment_data.get('id', 'unknown')}: {e}")
                        stats['errors'] += 1
                        continue
            
            logger.info(f"✅ Fulfillment orders sync completed: {stats}")
            
            return {
                'success': True,
                'message': f"Synced {stats['total']} fulfillment orders successfully",
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Fulfillment orders sync failed: {e}")
            return {
                'success': False,
                'message': f"Fulfillment orders sync failed: {str(e)}",
                'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 1}
            }
    
    def _sync_single_fulfillment_order(self, order: ShopifyOrder, fulfillment_data: Dict) -> Dict:
        """
        Sync a single fulfillment order
        """
        fulfillment_id = fulfillment_data['id']
        
        # Parse timestamps
        created_at = parse_datetime(fulfillment_data.get('createdAt'))
        updated_at = parse_datetime(fulfillment_data.get('updatedAt'))
        fulfill_at = parse_datetime(fulfillment_data.get('fulfillAt')) if fulfillment_data.get('fulfillAt') else None
        fulfill_by = parse_datetime(fulfillment_data.get('fulfillBy')) if fulfillment_data.get('fulfillBy') else None
        
        # Get location information
        assigned_location = fulfillment_data.get('assignedLocation', {})
        location_shopify_id = assigned_location.get('id') if assigned_location else None
        
        # Get location object
        location = None
        if location_shopify_id:
            try:
                from inventory.models import ShopifyLocation
                location = ShopifyLocation.objects.get(shopify_id=location_shopify_id)
            except ShopifyLocation.DoesNotExist:
                logger.warning(f"Location {location_shopify_id} not found for fulfillment {fulfillment_id}")
        
        # Create or update fulfillment order
        fulfillment_order, created = ShopifyFulfillmentOrder.objects.update_or_create(
            shopify_id=fulfillment_id,
            defaults={
                'order': order,
                'location': location,
                'status': fulfillment_data.get('status', 'open'),
                'request_status': fulfillment_data.get('requestStatus', 'unsubmitted'),
                'fulfill_at': fulfill_at,
                'fulfill_by': fulfill_by,
                'international_duties': fulfillment_data.get('internationalDuties'),
                'delivery_method': fulfillment_data.get('deliveryMethod'),
                'created_at': created_at,
                'updated_at': updated_at,
                'store_domain': self.store_domain,
            }
        )
        
        if created:
            logger.info(f"✅ Created fulfillment order: {fulfillment_id}")
        else:
            logger.info(f"📝 Updated fulfillment order: {fulfillment_id}")
        
        return {
            'created': created,
            'fulfillment_order': fulfillment_order
        }
    
    def get_fulfillment_statistics(self) -> Dict:
        """
        Get fulfillment synchronization statistics
        """
        total_fulfillments = ShopifyFulfillmentOrder.objects.count()
        
        # Recent syncs (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_fulfillments = ShopifyFulfillmentOrder.objects.filter(
            created_at__gte=recent_cutoff
        ).count()
        
        # Status breakdown
        status_counts = {}
        request_status_counts = {}
        
        for status_choice in ShopifyFulfillmentOrder.STATUS_CHOICES:
            status = status_choice[0]
            count = ShopifyFulfillmentOrder.objects.filter(status=status).count()
            if count > 0:
                status_counts[status] = count
        
        for status_choice in ShopifyFulfillmentOrder.REQUEST_STATUS_CHOICES:
            status = status_choice[0]
            count = ShopifyFulfillmentOrder.objects.filter(request_status=status).count()
            if count > 0:
                request_status_counts[status] = count
        
        return {
            'total_fulfillments': total_fulfillments,
            'recent_syncs_24h': recent_fulfillments,
            'status_breakdown': status_counts,
            'request_status_breakdown': request_status_counts,
            'store_domain': self.store_domain,
            'last_check': datetime.now().isoformat()
        }


# Convenience function for easy import
def sync_fulfillment_from_webhook(webhook_data: Dict) -> bool:
    """
    Convenience function to sync fulfillment from webhook
    """
    service = FulfillmentSyncService()
    return service.sync_fulfillment_from_webhook(webhook_data)


def get_fulfillment_sync_stats() -> Dict:
    """
    Convenience function to get fulfillment sync statistics
    """
    service = FulfillmentSyncService()
    return service.get_fulfillment_statistics()