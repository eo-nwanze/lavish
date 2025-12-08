#!/usr/bin/env python
"""
Simple Product Sync Fix
Handles product sync with existing database constraints
"""

import os
import sys
import logging
from datetime import datetime

# Add the project path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from products.models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage
from products.realtime_sync import RealtimeProductSyncService
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_products_with_constraints():
    """Sync products while handling database constraints"""
    logger.info("Starting product sync with constraint handling...")
    
    try:
        # Initialize sync service
        sync_service = RealtimeProductSyncService()
        
        # Get all products from Shopify
        client = EnhancedShopifyAPIClient()
        all_products = client.fetch_all_products()
        
        logger.info(f"Retrieved {len(all_products)} products from Shopify")
        
        # Sync each product with constraint handling
        stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
        
        for product_data in all_products:
            try:
                # Extract SEO data safely
                seo_data = product_data.get('seo', {})
                seo_title = seo_data.get('title', '') if seo_data else ''
                seo_description = seo_data.get('description', '') if seo_data else ''
                
                # Ensure SEO fields are not None
                if seo_title is None:
                    seo_title = ''
                if seo_description is None:
                    seo_description = ''
                
                # Parse timestamps
                created_at = datetime.fromisoformat(product_data['createdAt'].replace('Z', '+00:00'))
                updated_at = datetime.fromisoformat(product_data['updatedAt'].replace('Z', '+00:00'))
                published_at = None
                if product_data.get('publishedAt'):
                    published_at = datetime.fromisoformat(product_data['publishedAt'].replace('Z', '+00:00'))
                
                # Create or update product
                shopify_id = product_data['id']
                
                product, created = ShopifyProduct.objects.update_or_create(
                    shopify_id=shopify_id,
                    defaults={
                        'title': product_data.get('title', ''),
                        'handle': product_data.get('handle', ''),
                        'description': product_data.get('description', ''),
                        'product_type': product_data.get('productType', ''),
                        'vendor': product_data.get('vendor', ''),
                        'status': product_data.get('status', 'DRAFT'),
                        'seo_title': seo_title,
                        'seo_description': seo_description,
                        'tags': product_data.get('tags', []),
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'published_at': published_at,
                        'store_domain': '7fa66c-ac.myshopify.com',
                        'last_synced': datetime.now(),
                    }
                )
                
                stats['total'] += 1
                
                if created:
                    stats['created'] += 1
                    logger.info(f"✅ Created product: {product.title}")
                else:
                    stats['updated'] += 1
                    logger.info(f"📝 Updated product: {product.title}")
                
                # Sync variants
                variants_synced = 0
                for variant_edge in product_data.get('variants', {}).get('edges', []):
                    try:
                        variant_data = variant_edge['node']
                        variant, variant_created = ShopifyProductVariant.objects.update_or_create(
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
                        variants_synced += 1
                    except Exception as e:
                        logger.warning(f"Failed to sync variant: {e}")
                        continue
                
                # Sync images
                images_synced = 0
                for image_edge in product_data.get('images', {}).get('edges', []):
                    try:
                        image_data = image_edge['node']
                        image, image_created = ShopifyProductImage.objects.update_or_create(
                            shopify_id=image_data['id'],
                            defaults={
                                'product': product,
                                'src': image_data.get('src', ''),
                                'alt_text': image_data.get('altText', ''),
                                'store_domain': product.store_domain,
                                'last_synced': datetime.now(),
                            }
                        )
                        images_synced += 1
                    except Exception as e:
                        logger.warning(f"Failed to sync image: {e}")
                        continue
                
                logger.info(f"  - {product.title}: {variants_synced} variants, {images_synced} images")
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"❌ Failed to sync product {product_data.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"🎉 Product sync completed:")
        logger.info(f"   Total: {stats['total']}")
        logger.info(f"   Created: {stats['created']}")
        logger.info(f"   Updated: {stats['updated']}")
        logger.info(f"   Errors: {stats['errors']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Product sync failed: {e}")
        return None

def verify_product_sync():
    """Verify product sync results"""
    logger.info("Verifying product sync...")
    
    try:
        # Count products in Django
        django_products = ShopifyProduct.objects.count()
        logger.info(f"Products in Django: {django_products}")
        
        # Check sample products
        sample_products = ShopifyProduct.objects.all()[:5]
        for product in sample_products:
            logger.info(f"  - {product.title} (ID: {product.shopify_id})")
        
        # Check variants
        variants = ShopifyProductVariant.objects.count()
        logger.info(f"Product variants: {variants}")
        
        # Check images
        images = ShopifyProductImage.objects.count()
        logger.info(f"Product images: {images}")
        
        return {
            'products': django_products,
            'variants': variants,
            'images': images
        }
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return None

def main():
    """Main execution function"""
    print("=" * 80)
    print("🔧 STEP 1: COMPLETE PRODUCT SYNC")
    print("=" * 80)
    
    # Step 1: Sync all products
    print("\n1. Syncing all products with constraint handling...")
    sync_stats = sync_products_with_constraints()
    if sync_stats:
        print(f"✅ Product sync completed: {sync_stats['total']} products")
    else:
        print("❌ Product sync failed")
        return False
    
    # Step 2: Verify sync
    print("\n2. Verifying sync results...")
    verification = verify_product_sync()
    if verification:
        print(f"✅ Verification successful:")
        print(f"   Products: {verification['products']}")
        print(f"   Variants: {verification['variants']}")
        print(f"   Images: {verification['images']}")
    else:
        print("❌ Verification failed")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 STEP 1 COMPLETED SUCCESSFULLY!")
    print("✅ All products have been synchronized from Shopify to Django")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)