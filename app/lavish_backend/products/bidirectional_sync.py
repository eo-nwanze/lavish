"""
Bidirectional Product Sync Service
Handles Django → Shopify product synchronization
"""

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('products')


class ProductBidirectionalSync:
    """Service for syncing products from Django to Shopify"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def push_product_to_shopify(self, product) -> Dict:
        """
        Push a Django product to Shopify
        
        Args:
            product: ShopifyProduct instance
            
        Returns:
            Dict with success status and details
        """
        try:
            # Check if product has a valid Shopify ID (not temp/test)
            has_valid_id = (product.shopify_id and 
                          product.shopify_id.startswith('gid://shopify/Product/') and
                          not product.shopify_id.startswith('gid://shopify/Product/test'))
            
            # If has temp/test ID, treat as new product
            if (product.shopify_id and 
                (product.shopify_id.startswith('test_') or 
                 product.shopify_id.startswith('temp_') or
                 product.shopify_id.startswith('gid://shopify/Product/test'))):
                logger.info(f"Product {product.id} has test/temp ID, will create in Shopify")
                return self._create_new_product(product)
            
            # Check if this is a new product or update based on Shopify ID
            if has_valid_id:
                # Product already exists in Shopify, update it
                logger.info(f"Product {product.id} has valid Shopify ID, will update in Shopify")
                return self._update_existing_product(product)
            else:
                # New product, create in Shopify
                logger.info(f"Product {product.id} has no valid Shopify ID, will create in Shopify")
                return self._create_new_product(product)
                
        except Exception as e:
            logger.error(f"Error pushing product {product.id} to Shopify: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to push product: {e}"
            }
    
    def _create_new_product(self, product) -> Dict:
        """Create a new product in Shopify"""
        from products.models import ShopifyProduct
        
        # Prepare variants data
        variants = []
        if product.variants.exists():
            for variant in product.variants.all():
                variants.append({
                    "title": variant.title,
                    "price": str(variant.price),
                    "sku": variant.sku or "",
                    "inventory_quantity": variant.inventory_quantity or 0,
                })
        else:
            # Create a default variant if none exist
            variants.append({
                "title": "Default",
                "price": "0.00",
                "sku": "",
                "inventory_quantity": 0,
            })
        
        # Prepare images data
        images = []
        if product.images.exists():
            for image in product.images.all():
                images.append({
                    "src": image.src,
                    "alt": image.alt_text or "",
                })
        
        # Prepare tags
        tags = product.get_tags_list() if hasattr(product, 'get_tags_list') else []
        
        # Create product in Shopify
        result = self.client.create_product_in_shopify(
            title=product.title,
            description=product.description,
            vendor=product.vendor or "",
            product_type=product.product_type or "",
            tags=tags,
            variants=variants,
            images=images,
            status=product.status or "DRAFT"
        )
        
        if result.get("success"):
            # Update Django product with Shopify ID
            shopify_product = result.get("product", {})
            shopify_id = shopify_product.get("id", "")
            handle = shopify_product.get("handle", "")
            
            with transaction.atomic():
                product.shopify_id = shopify_id
                product.handle = handle
                product.needs_shopify_push = False
                product.shopify_push_error = ""
                product.last_pushed_to_shopify = timezone.now()
                product.sync_status = 'synced'
                product.save()
                
                # Check if we have custom variants to create
                django_variants = list(product.variants.all())
                shopify_variants = shopify_product.get("variants", {}).get("edges", [])
                
                # If we have Django variants and they're not just a single default variant
                if len(django_variants) > 0:
                    # Check if this is a real custom variant or just default
                    needs_custom_variants = len(django_variants) > 1 or (
                        len(django_variants) == 1 and 
                        django_variants[0].title not in ['Default', 'Default Title']
                    )
                    
                    if needs_custom_variants:
                        logger.info(f"Creating {len(django_variants)} custom variants for product {shopify_id}")
                        
                        # Shopify automatically creates a "Default Title" variant
                        # We'll update that one for the first Django variant, and create new ones for the rest
                        default_variant_id = None
                        if shopify_variants:
                            default_variant_id = shopify_variants[0].get("node", {}).get("id")
                            logger.info(f"Found default variant: {default_variant_id}")
                        
                        # If we have only 1 Django variant, update the default Shopify variant
                        # If we have multiple, create the 2nd+ variants and update the first one
                        variants_to_create = []
                        if len(django_variants) > 1:
                            # Create variants for 2nd+  Django variants
                            variants_to_create = [
                                {
                                    "title": v.title,
                                    "price": float(v.price)
                                }
                                for v in django_variants[1:]  # Skip first variant
                            ]
                        
                        # Update the first Django variant to use the default Shopify variant
                        if default_variant_id and django_variants:
                            first_variant = django_variants[0]
                            first_variant.shopify_id = default_variant_id
                            first_variant.save()
                            
                            logger.info(f"Updating default variant {default_variant_id} for {first_variant.title}")
                            
                            # Update variant with Django data (price, SKU)
                            self.client.update_product_variant(
                                default_variant_id, 
                                sku=first_variant.sku,
                                price=float(first_variant.price)
                            )
                            
                            # Update inventory for this variant if it has quantity
                            if first_variant.inventory_quantity > 0:
                                self._update_variant_inventory(
                                    default_variant_id,
                                    first_variant.inventory_quantity,
                                    variant_model=first_variant
                                )
                        
                        # Now create additional variants if we have more than 1
                        if variants_to_create:
                            create_result = self.client.create_product_variants(shopify_id, variants_to_create)
                            
                            if create_result.get("success"):
                                created_variants = create_result.get("variants", [])
                                logger.info(f"Successfully created {len(created_variants)} additional variants")
                                
                                # Match created variants to Django variants (starting from index 1)
                                for idx, created_variant in enumerate(created_variants):
                                    django_idx = idx + 1  # Skip first variant (already handled)
                                    if django_idx < len(django_variants):
                                        django_variant = django_variants[django_idx]
                                        shopify_variant_id = created_variant.get("id")
                                        django_variant.shopify_id = shopify_variant_id
                                        django_variant.save()
                                        
                                        logger.info(f"Matched Django variant {django_variant.title} to Shopify ID {shopify_variant_id}")
                                        
                                        # Update SKU if provided
                                        if django_variant.sku:
                                            logger.info(f"Setting SKU for variant {shopify_variant_id}: {django_variant.sku}")
                                            self.client.update_product_variant(shopify_variant_id, sku=django_variant.sku)
                                        
                                        # Update inventory for this variant if it has quantity
                                        if django_variant.inventory_quantity > 0:
                                            self._update_variant_inventory(
                                                shopify_variant_id,
                                                django_variant.inventory_quantity,
                                                variant_model=django_variant
                                            )
                            else:
                                logger.error(f"Failed to create additional variants: {create_result.get('message')}")
                    else:
                        # Just one default variant - use the one Shopify created
                        if shopify_variants and django_variants:
                            django_variant = django_variants[0]
                            variant_node = shopify_variants[0].get("node", {})
                            shopify_variant_id = variant_node.get("id", "")
                            django_variant.shopify_id = shopify_variant_id
                            django_variant.save()
                            
                            if django_variant.inventory_quantity > 0:
                                self._update_variant_inventory(
                                    shopify_variant_id,
                                    django_variant.inventory_quantity,
                                    variant_model=django_variant
                                )
                else:
                    # No Django variants - just use Shopify's default
                    if shopify_variants:
                        logger.info("No Django variants, using Shopify default variant")
            
            logger.info(f"Successfully created product {product.id} in Shopify: {shopify_id}")
            return {
                "success": True,
                "shopify_id": shopify_id,
                "message": f"Product '{product.title}' created in Shopify"
            }
        else:
            # Save error to product
            error_msg = result.get("message", "Unknown error")
            product.shopify_push_error = error_msg
            product.sync_status = 'error'
            product.save()
            
            return result
    
    def _update_existing_product(self, product) -> Dict:
        """Update an existing product in Shopify"""
        tags = product.get_tags_list() if hasattr(product, 'get_tags_list') else []
        
        result = self.client.update_product_in_shopify(
            shopify_product_id=product.shopify_id,
            title=product.title,
            description=product.description,
            vendor=product.vendor,
            product_type=product.product_type,
            tags=tags,
            status=product.status
        )
        
        if result.get("success"):
            with transaction.atomic():
                product.needs_shopify_push = False
                product.shopify_push_error = ""
                product.last_pushed_to_shopify = timezone.now()
                product.sync_status = 'synced'
                product.save()
                
                # Also update variant inventory if variants exist
                for variant in product.variants.all():
                    if variant.shopify_id and variant.shopify_id.startswith('gid://shopify/ProductVariant/'):
                        if variant.inventory_quantity > 0:
                            self._update_variant_inventory(
                                variant.shopify_id,
                                variant.inventory_quantity,
                                variant_model=variant
                            )
            
            logger.info(f"Successfully updated product {product.id} in Shopify")
            return {
                "success": True,
                "message": f"Product '{product.title}' updated in Shopify"
            }
        else:
            # Save error to product
            error_msg = result.get("message", "Unknown error")
            product.shopify_push_error = error_msg
            product.sync_status = 'error'
            product.save()
            
            return result
    
    def delete_product_from_shopify(self, product) -> Dict:
        """Delete a product from Shopify"""
        if not product.shopify_id:
            return {
                "success": False,
                "message": "Product has no Shopify ID, cannot delete"
            }
        
        result = self.client.delete_product_in_shopify(product.shopify_id)
        
        if result.get("success"):
            logger.info(f"Successfully deleted product {product.id} from Shopify")
            # Optionally delete from Django too, or just clear the shopify_id
            product.shopify_id = ""
            product.sync_status = 'synced'
            product.save()
        
        return result
    
    def bulk_push_products(self, product_ids: List[int]) -> Dict:
        """
        Push multiple products to Shopify
        
        Args:
            product_ids: List of ShopifyProduct IDs
            
        Returns:
            Dict with results summary
        """
        from products.models import ShopifyProduct
        
        products = ShopifyProduct.objects.filter(id__in=product_ids)
        
        results = {
            "total": len(product_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for product in products:
            result = self.push_product_to_shopify(product)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "product_id": product.id,
                    "product_title": product.title,
                    "error": result.get("message", "Unknown error")
                })
        
        return results
    
    def _enable_inventory_tracking(self, inventory_item_id: str) -> Dict:
        """
        Enable inventory tracking for an inventory item
        
        Args:
            inventory_item_id: Shopify inventory item ID
            
        Returns:
            Dict with success status
        """
        try:
            mutation = """
            mutation inventoryItemUpdate($id: ID!, $input: InventoryItemInput!) {
              inventoryItemUpdate(id: $id, input: $input) {
                inventoryItem {
                  id
                  tracked
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            
            result = self.client.execute_graphql_query(
                mutation,
                {
                    "id": inventory_item_id,
                    "input": {"tracked": True}
                }
            )
            
            errors = result.get("data", {}).get("inventoryItemUpdate", {}).get("userErrors", [])
            
            if errors:
                logger.error(f"Error enabling inventory tracking: {errors}")
                return {
                    "success": False,
                    "message": f"Failed to enable tracking: {errors[0]['message']}"
                }
            
            logger.info(f"Successfully enabled inventory tracking for {inventory_item_id}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Exception enabling inventory tracking: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to enable tracking: {e}"
            }
    
    def _create_django_inventory_records(self, variant, inventory_item_id: str, location_id: str, quantity: int):
        """
        Create Django inventory item and level records
        
        Args:
            variant: ShopifyProductVariant instance
            inventory_item_id: Shopify inventory item ID
            location_id: Shopify location ID
            quantity: Inventory quantity
        """
        from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel, ShopifyLocation
        
        try:
            # Get or create location
            location, created = ShopifyLocation.objects.get_or_create(
                shopify_id=location_id,
                defaults={
                    'name': 'Primary Location',
                    'active': True
                }
            )
            
            if created:
                logger.info(f"Created new location: {location_id}")
            
            # Create or update inventory item
            inv_item, created = ShopifyInventoryItem.objects.get_or_create(
                shopify_id=inventory_item_id,
                defaults={
                    'variant': variant,
                    'tracked': True,
                    'requires_shipping': variant.requires_shipping,
                    'sku': variant.sku
                }
            )
            
            if not created:
                inv_item.tracked = True
                inv_item.variant = variant
                inv_item.save()
                logger.info(f"Updated inventory item: {inventory_item_id}")
            else:
                logger.info(f"Created inventory item: {inventory_item_id}")
            
            # Create or update inventory level
            inv_level, created = ShopifyInventoryLevel.objects.get_or_create(
                inventory_item=inv_item,
                location=location,
                defaults={
                    'available': quantity,
                    'updated_at': timezone.now(),
                    'needs_shopify_push': False
                }
            )
            
            if not created:
                inv_level.available = quantity
                inv_level.updated_at = timezone.now()
                inv_level.needs_shopify_push = False
                inv_level.save(skip_push_flag=True)
                logger.info(f"Updated inventory level for {variant.title}")
            else:
                logger.info(f"Created inventory level for {variant.title}")
            
        except Exception as e:
            logger.error(f"Exception creating Django inventory records: {e}")
    
    def _update_variant_inventory(self, variant_id: str, quantity: int, variant_model=None) -> Dict:
        """
        Update inventory quantity for a variant in Shopify
        Also enables inventory tracking and creates Django records
        
        Args:
            variant_id: Shopify variant ID (gid://shopify/ProductVariant/...)
            quantity: Inventory quantity to set
            variant_model: Django variant model instance (optional, for creating inventory records)
            
        Returns:
            Dict with success status
        """
        try:
            # First, fetch the inventory item ID and location from the variant
            query = """
            query getVariantInventoryItem($id: ID!) {
              productVariant(id: $id) {
                id
                inventoryItem {
                  id
                  tracked
                  inventoryLevels(first: 1) {
                    edges {
                      node {
                        id
                        location {
                          id
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            result = self.client.execute_graphql_query(query, {"id": variant_id})
            
            if "errors" in result:
                logger.error(f"Error fetching inventory item: {result['errors']}")
                return {
                    "success": False,
                    "message": "Failed to fetch inventory item ID"
                }
            
            variant_data = result.get("data", {}).get("productVariant", {})
            inventory_item = variant_data.get("inventoryItem", {})
            inventory_item_id = inventory_item.get("id")
            
            if not inventory_item_id:
                logger.warning(f"No inventory item found for variant {variant_id}")
                return {
                    "success": False,
                    "message": "No inventory item found"
                }
            
            # Get location
            levels = inventory_item.get("inventoryLevels", {}).get("edges", [])
            location_id = None
            location_name = None
            
            if levels:
                location = levels[0].get("node", {}).get("location", {})
                location_id = location.get("id")
                location_name = location.get("name")
            
            # Enable inventory tracking if not already enabled
            if not inventory_item.get("tracked"):
                logger.info(f"Enabling inventory tracking for {variant_id}")
                track_result = self._enable_inventory_tracking(inventory_item_id)
                if not track_result.get("success"):
                    logger.warning(f"Failed to enable tracking but continuing: {track_result.get('message')}")
            
            # Now update the inventory quantity
            update_result = self.client.update_inventory_quantities(
                inventory_item_id=inventory_item_id,
                available_quantity=quantity,
                location_id=location_id
            )
            
            if update_result.get("success"):
                logger.info(f"Successfully updated inventory for variant {variant_id} to {quantity}")
                
                # Create Django inventory records if variant model provided
                if variant_model and location_id:
                    self._create_django_inventory_records(
                        variant_model,
                        inventory_item_id,
                        location_id,
                        quantity
                    )
            else:
                logger.warning(f"Failed to update inventory for variant {variant_id}: {update_result.get('message')}")
            
            return update_result
            
        except Exception as e:
            logger.error(f"Exception updating variant inventory: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update inventory: {e}"
            }

    def sync_pending_products(self) -> Dict:
        """
        Sync all products that need to be pushed to Shopify
        
        Returns:
            Dict with results summary
        """
        from products.models import ShopifyProduct
        
        pending_products = ShopifyProduct.objects.filter(needs_shopify_push=True)
        
        results = {
            "total": pending_products.count(),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for product in pending_products:
            result = self.push_product_to_shopify(product)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "product_id": product.id,
                    "product_title": product.title,
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"Bulk sync completed: {results['successful']}/{results['total']} successful")
        return results


# Singleton instance
bidirectional_sync = ProductBidirectionalSync()
