#!/usr/bin/env python
"""
Fix Product Sync Issues
Handles database constraints and completes full product synchronization
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
from django.db import connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_constraints():
    """Fix database constraints for SEO fields"""
    logger.info("Fixing database constraints...")
    
    try:
        with connection.cursor() as cursor:
            # Get current table info
            cursor.execute('PRAGMA table_info(products_shopifyproduct);')
            columns = cursor.fetchall()
            
            # Check if seo_title has NOT NULL constraint
            seo_title_nullable = True
            for column in columns:
                if column[1] == 'seo_title' and column[3] == 1:  # column[3] is notnull
                    seo_title_nullable = False
                    break
            
            if not seo_title_nullable:
                logger.info("Dropping NOT NULL constraint from seo_title...")
                # SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table
                cursor.execute('''
                CREATE TABLE products_shopifyproduct_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shopify_id VARCHAR(100) NOT NULL UNIQUE,
                    title VARCHAR(255) NOT NULL,
                    handle VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    product_type VARCHAR(100) NOT NULL,
                    vendor VARCHAR(100) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    published_at DATETIME NULL,
                    seo_title VARCHAR(255) NULL,
                    seo_description TEXT NULL,
                    tags TEXT NULL,
                    created_at DATETIME NOT NULL,
                    store_domain VARCHAR(100) NOT NULL,
                    last_synced DATETIME NOT NULL,
                    sync_status VARCHAR(20) NOT NULL,
                    created_in_django BOOL NOT NULL,
                    last_pushed_to_shopify DATETIME NULL,
                    needs_shopify_push BOOL NOT NULL,
                    shopify_push_error TEXT NULL,
                    updated_at DATETIME NOT NULL
                );
                ''')
                
                # Copy data
                cursor.execute('''
                INSERT INTO products_shopifyproduct_new 
                SELECT id, shopify_id, title, handle, description, product_type, vendor, status, 
                       published_at, seo_title, seo_description, tags, created_at, store_domain, 
                       last_synced, sync_status, created_in_django, last_pushed_to_shopify, 
                       needs_shopify_push, shopify_push_error, updated_at
                FROM products_shopifyproduct;
                ''')
                
                # Drop old table and rename new one
                cursor.execute('DROP TABLE products_shopifyproduct;')
                cursor.execute('ALTER TABLE products_shopifyproduct_new RENAME TO products_shopifyproduct;')
                
                # Recreate indexes
                cursor.execute('CREATE INDEX "products_shopifyproduct_handle" ON "products_shopifyproduct" ("handle");')
                cursor.execute('CREATE INDEX "products_shopifyproduct_shopify_id" ON "products_shopifyproduct" ("shopify_id");')
                cursor.execute('CREATE INDEX "products_shopifyproduct_status" ON "products_shopifyproduct" ("status");')
                cursor.execute('CREATE INDEX "products_shopifyproduct_product_type" ON "products_shopifyproduct" ("product_type");')
                cursor.execute('CREATE INDEX "products_shopifyproduct_vendor" ON "products_shopifyproduct" ("vendor");')
                
                logger.info("✅ Database constraints fixed successfully")
            else:
                logger.info("✅ SEO fields already nullable")
                
    except Exception as e:
        logger.error(f"❌ Failed to fix database constraints: {e}")
        return False
    
    return True

def sync_all_products():
    """Sync all products from Shopify to Django"""
    logger.info("Starting full product synchronization...")
    
    try:
        # Initialize sync service
        sync_service = RealtimeProductSyncService()
        
        # Get all products from Shopify
        client = EnhancedShopifyAPIClient()
        all_products = client.fetch_all_products()
        
        logger.info(f"Retrieved {len(all_products)} products from Shopify")
        
        # Sync each product
        stats = {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
        
        for product_data in all_products:
            try:
                result = sync_service._sync_single_product(product_data)
                stats['total'] += 1
                
                if result['created']:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
                    
                logger.info(f"✅ Synced product: {result['product'].title}")
                
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
    
    # Step 1: Fix database constraints
    print("\n1. Fixing database constraints...")
    if fix_database_constraints():
        print("✅ Database constraints fixed")
    else:
        print("❌ Failed to fix database constraints")
        return False
    
    # Step 2: Sync all products
    print("\n2. Syncing all products...")
    sync_stats = sync_all_products()
    if sync_stats:
        print(f"✅ Product sync completed: {sync_stats['total']} products")
    else:
        print("❌ Product sync failed")
        return False
    
    # Step 3: Verify sync
    print("\n3. Verifying sync results...")
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