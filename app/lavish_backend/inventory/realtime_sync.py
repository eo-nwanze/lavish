"""
Real-time Inventory Sync Service
Based on proven 7fa66cac patterns for live data synchronization
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.conf import settings

from .models import ShopifyLocation, ShopifyInventoryItem, ShopifyInventoryLevel, InventoryAdjustment, InventorySyncLog
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('inventory.realtime_sync')


class RealtimeInventorySyncService:
    """
    Real-time inventory synchronization service
    Provides live data refresh capabilities based on 7fa66cac patterns
    """
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
    
    def sync_all_inventory(self, limit: Optional[int] = None) -> Dict:
        """
        Sync all inventory items from Shopify with real-time data refresh
        """
        logger.info("🔄 Starting real-time inventory sync...")
        
        try:
            # Fetch inventory items using enhanced client
            inventory_data = self.client.fetch_all_inventory_items(limit=limit)
            
            if not inventory_data:
                return {
                    'success': False,
                    'message': 'No inventory items retrieved from Shopify',
                    'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
                }
            
            # Process inventory items in batches
            stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0, 'levels': 0, 'locations': 0}
            
            with transaction.atomic():
                for item_data in inventory_data:
                    try:
                        result = self._sync_single_inventory_item(item_data)
                        stats['total'] += 1
                        stats['levels'] += result['levels_synced']
                        stats['locations'] += result['locations_synced']
                        
                        if result['created']:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error syncing inventory item {item_data.get('id', 'unknown')}: {e}")
                        stats['errors'] += 1
                        continue
            
            logger.info(f"✅ Inventory sync completed: {stats}")
            
            return {
                'success': True,
                'message': f"Synced {stats['total']} inventory items successfully",
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Inventory sync failed: {e}")
            return {
                'success': False,
                'message': f"Inventory sync failed: {str(e)}",
                'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 1}
            }
    
    def _sync_single_inventory_item(self, item_data: Dict) -> Dict:
        """
        Sync a single inventory item with real-time data
        """
        shopify_id = item_data['id']
        
        # Parse timestamps
        created_at = parse_datetime(item_data.get('createdAt'))
        updated_at = parse_datetime(item_data.get('updatedAt'))
        
        # Extract variant information
        variant_data = item_data.get('variant', {})
        product_data = variant_data.get('product', {}) if variant_data else {}
        
        # Create or update inventory item
        inventory_item, created = ShopifyInventoryItem.objects.update_or_create(
            shopify_id=shopify_id,
            defaults={
                'sku': item_data.get('sku', ''),
                'tracked': item_data.get('tracked', False),
                'requires_shipping': item_data.get('requiresShipping', True),
                'variant_shopify_id': variant_data.get('id', ''),
                'variant_title': variant_data.get('title', ''),
                'variant_price': variant_data.get('price', '0.00'),
                'product_shopify_id': product_data.get('id', ''),
                'product_title': product_data.get('title', ''),
                'created_at': created_at,
                'updated_at': updated_at,
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        # Sync inventory levels and locations
        levels_synced = 0
        locations_synced = 0
        location_ids_seen = set()
        
        for level_edge in item_data.get('inventoryLevels', {}).get('edges', []):
            try:
                level_data = level_edge['node']
                location_data = level_data.get('location', {})
                
                # Sync location first
                if location_data.get('id') not in location_ids_seen:
                    self._sync_location(location_data)
                    locations_synced += 1
                    location_ids_seen.add(location_data.get('id'))
                
                # Sync inventory level
                self._sync_inventory_level(inventory_item, level_data)
                levels_synced += 1
                
            except Exception as e:
                logger.warning(f"Failed to sync inventory level for item {shopify_id}: {e}")
                continue
        
        if created:
            logger.info(f"✅ Created inventory item: {inventory_item.sku} with {levels_synced} levels across {locations_synced} locations")
        else:
            logger.info(f"📝 Updated inventory item: {inventory_item.sku} with {levels_synced} levels across {locations_synced} locations")
        
        return {
            'created': created,
            'inventory_item': inventory_item,
            'levels_synced': levels_synced,
            'locations_synced': locations_synced
        }
    
    def _sync_location(self, location_data: Dict):
        """
        Sync a location
        """
        if not location_data.get('id'):
            return None, False
        
        location, created = ShopifyLocation.objects.update_or_create(
            shopify_id=location_data['id'],
            defaults={
                'name': location_data.get('name', ''),
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return location, created
    
    def _sync_inventory_level(self, inventory_item: ShopifyInventoryItem, level_data: Dict):
        """
        Sync an inventory level
        """
        location_data = level_data.get('location', {})
        
        # Get or create location
        location, _ = ShopifyLocation.objects.get_or_create(
            shopify_id=location_data.get('id', ''),
            defaults={
                'name': location_data.get('name', ''),
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        # Create or update inventory level
        inventory_level, created = ShopifyInventoryLevel.objects.update_or_create(
            inventory_item=inventory_item,
            location=location,
            defaults={
                'available': level_data.get('available', 0),
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return inventory_level, created
    
    def sync_locations(self) -> Dict:
        """
        Sync all locations from Shopify
        Note: This would require a separate locations query in a real implementation
        """
        logger.info("🔄 Syncing locations...")
        
        # For now, locations are synced as part of inventory items
        # In a full implementation, you'd have a separate locations query
        
        total_locations = ShopifyLocation.objects.count()
        
        return {
            'success': True,
            'message': f"Currently tracking {total_locations} locations",
            'total_locations': total_locations
        }
    
    def get_sync_statistics(self) -> Dict:
        """
        Get synchronization statistics
        """
        total_items = ShopifyInventoryItem.objects.count()
        total_levels = ShopifyInventoryLevel.objects.count()
        total_locations = ShopifyLocation.objects.count()
        
        # Recent syncs (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_items = ShopifyInventoryItem.objects.filter(
            last_synced__gte=recent_cutoff
        ).count()
        
        # Inventory statistics
        from django.db.models import Sum, Count
        
        total_available = ShopifyInventoryLevel.objects.aggregate(
            total=Sum('available')
        )['total'] or 0
        
        tracked_items = ShopifyInventoryItem.objects.filter(tracked=True).count()
        
        # Low stock items (available < 10)
        low_stock_count = ShopifyInventoryLevel.objects.filter(available__lt=10).count()
        
        return {
            'total_inventory_items': total_items,
            'total_inventory_levels': total_levels,
            'total_locations': total_locations,
            'recent_syncs_24h': recent_items,
            'tracked_items': tracked_items,
            'total_available_inventory': total_available,
            'low_stock_items': low_stock_count,
            'store_domain': self.store_domain,
            'last_check': datetime.now().isoformat()
        }
    
    def get_low_stock_items(self, threshold: int = 10) -> List[Dict]:
        """
        Get inventory items with low stock
        """
        low_stock_levels = ShopifyInventoryLevel.objects.filter(
            available__lt=threshold
        ).select_related('inventory_item', 'location')
        
        low_stock_items = []
        for level in low_stock_levels:
            low_stock_items.append({
                'sku': level.inventory_item.sku,
                'product_title': level.inventory_item.product_title,
                'variant_title': level.inventory_item.variant_title,
                'location': level.location.name,
                'available': level.available,
                'last_synced': level.last_synced.isoformat() if level.last_synced else None
            })
        
        return low_stock_items


# Convenience function for easy import
def sync_inventory_realtime(limit: Optional[int] = None) -> Dict:
    """
    Convenience function to sync inventory in real-time
    """
    service = RealtimeInventorySyncService()
    return service.sync_all_inventory(limit=limit)


def get_inventory_sync_stats() -> Dict:
    """
    Convenience function to get sync statistics
    """
    service = RealtimeInventorySyncService()
    return service.get_sync_statistics()


def get_low_stock_alerts(threshold: int = 10) -> List[Dict]:
    """
    Convenience function to get low stock alerts
    """
    service = RealtimeInventorySyncService()
    return service.get_low_stock_items(threshold=threshold)
