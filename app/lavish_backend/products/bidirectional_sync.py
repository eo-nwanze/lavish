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
            # Check if this is a new product or update
            if product.shopify_id and not product.created_in_django:
                # Product already exists in Shopify, update it
                return self._update_existing_product(product)
            else:
                # New product, create in Shopify
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
                
                # Update variants with Shopify IDs
                shopify_variants = shopify_product.get("variants", {}).get("edges", [])
                for idx, edge in enumerate(shopify_variants):
                    variant_node = edge.get("node", {})
                    if idx < product.variants.count():
                        django_variant = product.variants.all()[idx]
                        django_variant.shopify_id = variant_node.get("id", "")
                        django_variant.save()
            
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
