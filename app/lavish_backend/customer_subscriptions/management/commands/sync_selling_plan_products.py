"""
Django Management Command: Sync Selling Plan Product Associations to Shopify

This command syncs product associations from Django to Shopify for all selling plans.
It ensures that the products associated with each selling plan in Django are also
associated with the corresponding selling plan group in Shopify.

Usage:
    python manage.py sync_selling_plan_products [--plan-id ID] [--dry-run]

Options:
    --plan-id ID    Sync only a specific selling plan by Django ID
    --dry-run       Show what would be synced without making changes
    --all           Sync all selling plans, including those without associations
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from customer_subscriptions.models import SellingPlan
from customer_subscriptions.bidirectional_sync import subscription_sync
import logging

logger = logging.getLogger('customer_subscriptions')


class Command(BaseCommand):
    help = 'Sync selling plan product associations from Django to Shopify'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-id',
            type=int,
            help='Sync only a specific selling plan by Django ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all selling plans, including those without product associations',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("SELLING PLAN PRODUCT SYNC"))
        self.stdout.write("=" * 80)
        
        # Get selling plans to sync
        if options['plan_id']:
            try:
                plans = SellingPlan.objects.filter(id=options['plan_id'])
                if not plans.exists():
                    self.stdout.write(self.style.ERROR(f"❌ Selling plan with ID {options['plan_id']} not found"))
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                return
        elif options['all']:
            plans = SellingPlan.objects.filter(is_active=True)
        else:
            # Default: only sync plans with products associated
            plans = SellingPlan.objects.filter(is_active=True, products__isnull=False).distinct()
        
        total_plans = plans.count()
        self.stdout.write(f"\nFound {total_plans} selling plan(s) to sync\n")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))
        
        # Stats tracking
        stats = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "total_products": 0,
            "errors": []
        }
        
        # Process each selling plan
        for plan in plans:
            self.stdout.write(f"\n{'-' * 80}")
            self.stdout.write(f"Plan: {plan.name} (ID: {plan.id})")
            self.stdout.write(f"   Shopify Group ID: {plan.shopify_selling_plan_group_id or 'NOT SYNCED'}")
            
            # Check if plan has Shopify group ID
            if not plan.shopify_selling_plan_group_id:
                self.stdout.write(self.style.WARNING("   Skipping: No Shopify group ID (plan not synced to Shopify yet)"))
                stats["skipped"] += 1
                continue
            
            # Get associated products
            products = plan.products.all()
            product_count = products.count()
            
            if product_count == 0:
                self.stdout.write(self.style.WARNING("   Skipping: No products associated with this plan"))
                stats["skipped"] += 1
                continue
            
            # Show products that will be synced
            self.stdout.write(f"   Products to sync: {product_count}")
            valid_products = [p for p in products if p.shopify_id and not p.shopify_id.startswith('temp_')]
            
            for idx, product in enumerate(valid_products[:5], 1):  # Show first 5
                self.stdout.write(f"      {idx}. {product.title}")
            
            if len(valid_products) > 5:
                self.stdout.write(f"      ... and {len(valid_products) - 5} more")
            
            invalid_count = product_count - len(valid_products)
            if invalid_count > 0:
                self.stdout.write(self.style.WARNING(f"   {invalid_count} product(s) without valid Shopify IDs (will be skipped)"))
            
            if len(valid_products) == 0:
                self.stdout.write(self.style.WARNING("   Skipping: No products with valid Shopify IDs"))
                stats["skipped"] += 1
                continue
            
            # Perform sync (or dry run)
            if options['dry_run']:
                self.stdout.write(self.style.SUCCESS(f"   Would sync {len(valid_products)} product(s) (DRY RUN)"))
                stats["successful"] += 1
                stats["total_products"] += len(valid_products)
            else:
                self.stdout.write("   Syncing to Shopify...")
                
                try:
                    result = subscription_sync.sync_selling_plan_products(plan)
                    
                    if result.get("success"):
                        products_added = result.get("products_added", 0)
                        total_products = result.get("total_products", 0)
                        self.stdout.write(self.style.SUCCESS(
                            f"   Success! Added {products_added} product(s). "
                            f"Total products in group now: {total_products}"
                        ))
                        stats["successful"] += 1
                        stats["total_products"] += products_added
                    else:
                        error_msg = result.get("message", "Unknown error")
                        self.stdout.write(self.style.ERROR(f"   Failed: {error_msg}"))
                        stats["failed"] += 1
                        stats["errors"].append(f"{plan.name}: {error_msg}")
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   Exception: {e}"))
                    stats["failed"] += 1
                    stats["errors"].append(f"{plan.name}: {str(e)}")
                    logger.exception(f"Error syncing selling plan products: {plan.name}")
        
        # Print summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("SYNC SUMMARY"))
        self.stdout.write("=" * 80)
        
        self.stdout.write(f"\nTotal Plans Processed: {total_plans}")
        self.stdout.write(self.style.SUCCESS(f"   Successful: {stats['successful']}"))
        
        if stats['failed'] > 0:
            self.stdout.write(self.style.ERROR(f"   Failed: {stats['failed']}"))
        
        if stats['skipped'] > 0:
            self.stdout.write(self.style.WARNING(f"   Skipped: {stats['skipped']}"))
        
        if not options['dry_run']:
            self.stdout.write(f"\nTotal Products Synced: {stats['total_products']}")
        
        # Show errors if any
        if stats['errors']:
            self.stdout.write(f"\nErrors ({len(stats['errors'])}):")
            for error in stats['errors'][:10]:  # Show first 10 errors
                self.stdout.write(f"   - {error}")
            
            if len(stats['errors']) > 10:
                self.stdout.write(f"   ... and {len(stats['errors']) - 10} more errors")
        
        self.stdout.write("\n" + "=" * 80)
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("\nDRY RUN COMPLETE - No changes were made"))
            self.stdout.write("Run without --dry-run to perform the actual sync\n")
        else:
            self.stdout.write(self.style.SUCCESS("\nSYNC COMPLETE"))
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Verify products are associated in Shopify Admin")
            self.stdout.write("2. Check product pages on your storefront")
            self.stdout.write("3. Confirm subscription options appear\n")

