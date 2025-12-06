"""
Bidirectional Inventory Sync Service
Handles Django ↔ Shopify inventory synchronization

Supports:
- Updating inventory in Django → Push to Shopify
- Importing inventory from Shopify → Save in Django  
- Real-time sync with signals
- Error handling and retry logic
"""

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from datetime import datetime

logger = logging.getLogger('inventory.bidirectional_sync')


class InventoryBidirectionalSync:
    """Service for syncing inventory levels between Django and Shopify"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def push_inventory_to_shopify(self, inventory_level) -> Dict:
        """
        Push inventory level changes from Django to Shopify
        
        Args:
            inventory_level: ShopifyInventoryLevel instance
            
        Returns:
            Dict with success status and details
        """
        from inventory.models import ShopifyInventoryLevel
        
        if not inventory_level.inventory_item.shopify_id:
            return {
                "success": False,
                "message": "Inventory item has no Shopify ID",
                "inventory_level_id": inventory_level.id
            }
        
        # Skip test/temp IDs
        if (inventory_level.inventory_item.shopify_id.startswith('test_') or 
            inventory_level.inventory_item.shopify_id.startswith('temp_')):
            error_msg = f"Cannot push inventory with test/temp ID: {inventory_level.inventory_item.shopify_id}"
            inventory_level.shopify_push_error = error_msg
            inventory_level.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "inventory_level_id": inventory_level.id
            }
        
        if not inventory_level.location.shopify_id:
            return {
                "success": False,
                "message": "Location has no Shopify ID",
                "inventory_level_id": inventory_level.id
            }
        
        # Skip test/temp location IDs
        if (inventory_level.location.shopify_id.startswith('test_') or 
            inventory_level.location.shopify_id.startswith('temp_')):
            error_msg = f"Cannot push inventory with test/temp location ID: {inventory_level.location.shopify_id}"
            inventory_level.shopify_push_error = error_msg
            inventory_level.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "inventory_level_id": inventory_level.id
            }
        
        # Use inventorySetQuantities mutation for precise control
        mutation = """
        mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
          inventorySetQuantities(input: $input) {
            inventoryAdjustmentGroup {
              id
              reason
              changes {
                name
                delta
                quantityAfterChange
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "reason": "correction",  # Options: correction, cycle_count_available, damaged, promotion, received, reservation, returned, quality_control, safety_stock, shrinkage
                "name": "available",  # Set the available quantity
                "ignoreCompareQuantity": True,  # Don't require compareQuantity for updates
                "quantities": [{
                    "inventoryItemId": inventory_level.inventory_item.shopify_id,
                    "locationId": inventory_level.location.shopify_id,
                    "quantity": inventory_level.available
                }]
            }
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                error_msg = str(result["errors"])
                logger.error(f"Inventory push failed: {error_msg}")
                inventory_level.shopify_push_error = error_msg
                inventory_level.save(update_fields=['shopify_push_error'])
                
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred",
                    "inventory_level_id": inventory_level.id
                }
            
            data = result.get("data", {}).get("inventorySetQuantities", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                error_msg = "; ".join([f"{e.get('field')}: {e.get('message')}" for e in user_errors])
                logger.error(f"Inventory validation errors: {error_msg}")
                inventory_level.shopify_push_error = error_msg
                inventory_level.save(update_fields=['shopify_push_error'])
                
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": error_msg,
                    "inventory_level_id": inventory_level.id
                }
            
            adjustment_group = data.get("inventoryAdjustmentGroup", {})
            
            if adjustment_group:
                # Success! Update the record
                inventory_level.needs_shopify_push = False
                inventory_level.shopify_push_error = ""
                inventory_level.last_pushed_to_shopify = timezone.now()
                inventory_level.save(update_fields=['needs_shopify_push', 'shopify_push_error', 'last_pushed_to_shopify'])
                
                logger.info(f"✅ Pushed inventory to Shopify: {inventory_level.inventory_item.sku} at {inventory_level.location.name} = {inventory_level.available}")
                
                return {
                    "success": True,
                    "message": "Inventory successfully pushed to Shopify",
                    "inventory_level_id": inventory_level.id,
                    "adjustment_group": adjustment_group
                }
            else:
                return {
                    "success": False,
                    "message": "No adjustment group returned",
                    "inventory_level_id": inventory_level.id
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Inventory push exception: {error_msg}")
            inventory_level.shopify_push_error = error_msg
            inventory_level.save(update_fields=['shopify_push_error'])
            
            return {
                "success": False,
                "message": f"Exception during push: {error_msg}",
                "inventory_level_id": inventory_level.id
            }
    
    def push_all_pending_inventory(self) -> Dict:
        """
        Push all inventory levels that need Shopify sync
        
        Returns:
            Dict with statistics about the operation
        """
        from inventory.models import ShopifyInventoryLevel
        
        pending_levels = ShopifyInventoryLevel.objects.filter(
            needs_shopify_push=True
        ).select_related('inventory_item', 'location')
        
        total = pending_levels.count()
        success_count = 0
        error_count = 0
        errors = []
        
        logger.info(f"🔄 Starting push of {total} pending inventory levels...")
        
        for level in pending_levels:
            result = self.push_inventory_to_shopify(level)
            
            if result["success"]:
                success_count += 1
            else:
                error_count += 1
                errors.append({
                    "inventory_level_id": level.id,
                    "sku": level.inventory_item.sku,
                    "location": level.location.name,
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"✅ Inventory push completed: {success_count} success, {error_count} errors out of {total} total")
        
        return {
            "success": error_count == 0,
            "total": total,
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    
    def pull_inventory_from_shopify(self, inventory_item_id: Optional[str] = None) -> Dict:
        """
        Pull inventory levels from Shopify
        
        Args:
            inventory_item_id: Optional Shopify inventory item ID to sync specific item
            
        Returns:
            Dict with sync statistics
        """
        from inventory.realtime_sync import sync_inventory_realtime
        
        # Use the existing realtime sync service for pulling
        return sync_inventory_realtime(limit=None)


# Convenience functions
def push_inventory_to_shopify(inventory_level) -> Dict:
    """Push a single inventory level to Shopify"""
    service = InventoryBidirectionalSync()
    return service.push_inventory_to_shopify(inventory_level)


def push_all_pending_inventory() -> Dict:
    """Push all pending inventory levels to Shopify"""
    service = InventoryBidirectionalSync()
    return service.push_all_pending_inventory()


def pull_inventory_from_shopify() -> Dict:
    """Pull inventory from Shopify"""
    service = InventoryBidirectionalSync()
    return service.pull_inventory_from_shopify()
