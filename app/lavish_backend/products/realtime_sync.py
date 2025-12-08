"""
Real-time Products Sync Service
Based on proven 7fa66cac patterns for live data synchronization
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.conf import settings

from .models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage, ShopifyProductMetafield, ProductSyncLog
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('products.realtime_sync')


class RealtimeProductSyncService:
    """
    Real-time product synchronization service
    Provides live data refresh capabilities based on 7fa66cac patterns
    """
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
        self.store_domain = settings.SHOPIFY_STORE_URL
    
    def sync_all_products(self, limit: Optional[int] = None) -> Dict:
        """
        Sync all products from Shopify with real-time data refresh
        """
        logger.info("🔄 Starting real-time product sync...")
        
        try:
            # Fetch products using enhanced client
            products_data = self.client.fetch_all_products(limit=limit)
            
            if not products_data:
                return {
                    'success': False,
                    'message': 'No products retrieved from Shopify',
                    'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
                }
            
            # Process products in batches
            stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0, 'variants': 0, 'images': 0}
            
            with transaction.atomic():
                for product_data in products_data:
                    try:
                        result = self._sync_single_product(product_data)
                        stats['total'] += 1
                        stats['variants'] += result['variants_synced']
                        stats['images'] += result['images_synced']
                        
                        if result['created']:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error syncing product {product_data.get('id', 'unknown')}: {e}")
                        stats['errors'] += 1
                        continue
            
            logger.info(f"✅ Product sync completed: {stats}")
            
            return {
                'success': True,
                'message': f"Synced {stats['total']} products successfully",
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Product sync failed: {e}")
            return {
                'success': False,
                'message': f"Product sync failed: {str(e)}",
                'stats': {'total': 0, 'created': 0, 'updated': 0, 'errors': 1}
            }
    
    def _sync_single_product(self, product_data: Dict) -> Dict:
        """
        Sync a single product with real-time data
        """
        shopify_id = product_data['id']
        
        # Parse timestamps
        created_at = parse_datetime(product_data.get('createdAt'))
        updated_at = parse_datetime(product_data.get('updatedAt'))
        published_at = parse_datetime(product_data.get('publishedAt')) if product_data.get('publishedAt') else None
        
        # Create or update product
        product, created = ShopifyProduct.objects.update_or_create(
            shopify_id=shopify_id,
            defaults={
                'title': product_data.get('title', ''),
                'handle': product_data.get('handle', ''),
                'description': product_data.get('description', ''),
                'vendor': product_data.get('vendor', ''),
                'product_type': product_data.get('productType', ''),
                'status': product_data.get('status', 'DRAFT'),
                'tags': product_data.get('tags', []),
                'seo_title': product_data.get('seo', {}).get('title', '') if product_data.get('seo') and product_data.get('seo', {}).get('title') else '',
                'seo_description': product_data.get('seo', {}).get('description', '') if product_data.get('seo') and product_data.get('seo', {}).get('description') else '',
                'created_at': created_at,
                'updated_at': updated_at,
                'published_at': published_at,
                'store_domain': self.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        # Sync variants
        variants_synced = 0
        for variant_edge in product_data.get('variants', {}).get('edges', []):
            try:
                self._sync_product_variant(product, variant_edge['node'])
                variants_synced += 1
            except Exception as e:
                logger.warning(f"Failed to sync variant for product {shopify_id}: {e}")
                continue
        
        # Sync images
        images_synced = 0
        for image_edge in product_data.get('images', {}).get('edges', []):
            try:
                self._sync_product_image(product, image_edge['node'])
                images_synced += 1
            except Exception as e:
                logger.warning(f"Failed to sync image for product {shopify_id}: {e}")
                continue
        
        if created:
            logger.info(f"✅ Created product: {product.title} with {variants_synced} variants, {images_synced} images")
        else:
            logger.info(f"📝 Updated product: {product.title} with {variants_synced} variants, {images_synced} images")
        
        return {
            'created': created,
            'product': product,
            'variants_synced': variants_synced,
            'images_synced': images_synced
        }
    
    def _sync_product_variant(self, product: ShopifyProduct, variant_data: Dict):
        """
        Sync a product variant
        """
        variant, created = ShopifyProductVariant.objects.update_or_create(
            shopify_id=variant_data['id'],
            defaults={
                'product': product,
                'title': variant_data.get('title', ''),
                'sku': variant_data.get('sku', ''),
                'price': variant_data.get('price', '0.00'),
                'compare_at_price': variant_data.get('compareAtPrice'),
                'inventory_quantity': variant_data.get('inventoryQuantity', 0),
                'inventory_item_id': variant_data.get('inventoryItem', {}).get('id', ''),
                'tracked': variant_data.get('inventoryItem', {}).get('tracked', False),
                'store_domain': product.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return variant, created
    
    def _sync_product_image(self, product: ShopifyProduct, image_data: Dict):
        """
        Sync a product image
        """
        image, created = ShopifyProductImage.objects.update_or_create(
            shopify_id=image_data['id'],
            defaults={
                'product': product,
                'src': image_data.get('src', ''),
                'alt_text': image_data.get('altText', ''),
                'store_domain': product.store_domain,
                'last_synced': datetime.now(),
            }
        )
        
        return image, created
    
    def get_sync_statistics(self) -> Dict:
        """
        Get synchronization statistics
        """
        total_products = ShopifyProduct.objects.count()
        total_variants = ShopifyProductVariant.objects.count()
        total_images = ShopifyProductImage.objects.count()
        
        # Recent syncs (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_products = ShopifyProduct.objects.filter(
            last_synced__gte=recent_cutoff
        ).count()
        
        # Status breakdown
        status_counts = {}
        for status_choice in ShopifyProduct.STATUS_CHOICES:
            status = status_choice[0]
            count = ShopifyProduct.objects.filter(status=status).count()
            if count > 0:
                status_counts[status] = count
        
        return {
            'total_products': total_products,
            'total_variants': total_variants,
            'total_images': total_images,
            'recent_syncs_24h': recent_products,
            'status_breakdown': status_counts,
            'store_domain': self.store_domain,
            'last_check': datetime.now().isoformat()
        }


# Convenience function for easy import
def sync_products_realtime(limit: Optional[int] = None) -> Dict:
    """
    Convenience function to sync products in real-time
    """
    service = RealtimeProductSyncService()
    return service.sync_all_products(limit=limit)


def get_product_sync_stats() -> Dict:
    """
    Convenience function to get sync statistics
    """
    service = RealtimeProductSyncService()
    return service.get_sync_statistics()
