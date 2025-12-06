"""
Django Management Command to Push Pending Changes to Shopify
This handles addresses and inventory that need to be synced
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from customers.models import ShopifyCustomerAddress
from inventory.models import ShopifyInventoryLevel
from customers.address_bidirectional_sync_fixed import push_address_to_shopify
from inventory.bidirectional_sync import push_inventory_to_shopify


class Command(BaseCommand):
    help = 'Push all pending customer addresses and inventory to Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--addresses-only',
            action='store_true',
            help='Only sync addresses',
        )
        parser.add_argument(
            '--inventory-only',
            action='store_true',
            help='Only sync inventory',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('PUSHING PENDING CHANGES TO SHOPIFY'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        addresses_only = options['addresses_only']
        inventory_only = options['inventory_only']
        
        # If neither flag is set, sync both
        sync_addresses = not inventory_only
        sync_inventory = not addresses_only

        # ==================== SYNC ADDRESSES ====================
        if sync_addresses:
            self.stdout.write('\n📍 Syncing Customer Addresses...')
            self.stdout.write('-' * 70)
            
            pending_addresses = ShopifyCustomerAddress.objects.filter(
                needs_shopify_push=True
            ).select_related('customer')
            
            total_addresses = pending_addresses.count()
            self.stdout.write(f'Found {total_addresses} addresses that need syncing')
            
            if total_addresses > 0:
                success_count = 0
                error_count = 0
                
                for address in pending_addresses:
                    customer_name = address.customer.full_name or address.customer.email
                    address_location = f"{address.city}, {address.province}" if address.city else "No location"
                    
                    self.stdout.write(f'\nProcessing: {customer_name} - {address_location}')
                    
                    # Check if customer has valid Shopify ID
                    if not address.customer.shopify_id:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Customer has no Shopify ID, skipping...'))
                        continue
                    
                    if (address.customer.shopify_id.startswith('test_') or 
                        address.customer.shopify_id.startswith('temp_')):
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Test/temp customer, skipping...'))
                        continue
                    
                    try:
                        result = push_address_to_shopify(address)
                        
                        if result['success']:
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Successfully synced'))
                            success_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'  ❌ Failed: {result.get("message", "Unknown error")}'))
                            error_count += 1
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Exception: {str(e)}'))
                        error_count += 1
                
                self.stdout.write('\n' + '-' * 70)
                self.stdout.write(self.style.SUCCESS(f'Address Sync Complete: {success_count} succeeded, {error_count} failed'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ No pending addresses to sync'))

        # ==================== SYNC INVENTORY ====================
        if sync_inventory:
            self.stdout.write('\n\n📊 Syncing Inventory Levels...')
            self.stdout.write('-' * 70)
            
            pending_inventory = ShopifyInventoryLevel.objects.filter(
                needs_shopify_push=True
            ).select_related('inventory_item', 'location')
            
            total_inventory = pending_inventory.count()
            self.stdout.write(f'Found {total_inventory} inventory levels that need syncing')
            
            if total_inventory > 0:
                success_count = 0
                error_count = 0
                
                for level in pending_inventory:
                    sku = level.inventory_item.sku or 'No SKU'
                    location = level.location.name or 'Unknown location'
                    
                    self.stdout.write(f'\nProcessing: {sku} at {location} ({level.available} units)')
                    
                    # Check if item has valid Shopify IDs
                    if not level.inventory_item.shopify_id:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  No Shopify inventory item ID, skipping...'))
                        continue
                    
                    if not level.location.shopify_id:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  No Shopify location ID, skipping...'))
                        continue
                    
                    if (level.inventory_item.shopify_id.startswith('test_') or 
                        level.inventory_item.shopify_id.startswith('temp_') or
                        level.location.shopify_id.startswith('test_') or
                        level.location.shopify_id.startswith('temp_')):
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Test/temp inventory, skipping...'))
                        continue
                    
                    try:
                        result = push_inventory_to_shopify(level)
                        
                        if result['success']:
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Successfully synced'))
                            success_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'  ❌ Failed: {result.get("message", "Unknown error")}'))
                            error_count += 1
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Exception: {str(e)}'))
                        error_count += 1
                
                self.stdout.write('\n' + '-' * 70)
                self.stdout.write(self.style.SUCCESS(f'Inventory Sync Complete: {success_count} succeeded, {error_count} failed'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ No pending inventory to sync'))

        # ==================== SUMMARY ====================
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('SYNC COMPLETED'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'Timestamp: {timezone.now()}')
        self.stdout.write('\n')
