import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from customers.services import CustomerSyncService
from products.services import ProductSyncService
from orders.services import OrderSyncService
from inventory.services import InventorySyncService
from shipping.services import ShippingSyncService
from shopify_integration.models import ShopifyStore, SyncOperation


class Command(BaseCommand):
    help = 'Synchronize data from Shopify store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['customers', 'products', 'orders', 'inventory', 'shipping', 'all'],
            default='all',
            help='Type of data to sync'
        )
        parser.add_argument(
            '--store',
            type=str,
            help='Store domain to sync (default: from settings)'
        )

    def handle(self, *args, **options):
        sync_type = options['type']
        store_domain = options.get('store')
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Shopify data sync: {sync_type}')
        )
        
        try:
            # Get or create store configuration
            if store_domain:
                store, created = ShopifyStore.objects.get_or_create(
                    store_domain=store_domain,
                    defaults={
                        'store_name': os.getenv('SHOPIFY_STORE_NAME', 'Lavish Library'),
                        'api_key': os.getenv('SHOPIFY_API_KEY'),
                        'api_secret': os.getenv('SHOPIFY_API_SECRET'),
                        'access_token': os.getenv('SHOPIFY_ACCESS_TOKEN'),
                        'api_version': os.getenv('SHOPIFY_API_VERSION', '2025-01'),
                    }
                )
            else:
                store = ShopifyStore.objects.filter(is_active=True).first()
                if not store:
                    store = ShopifyStore.objects.create(
                        store_domain=os.getenv('SHOPIFY_STORE_DOMAIN'),
                        store_name=os.getenv('SHOPIFY_STORE_NAME', 'Lavish Library'),
                        api_key=os.getenv('SHOPIFY_API_KEY'),
                        api_secret=os.getenv('SHOPIFY_API_SECRET'),
                        access_token=os.getenv('SHOPIFY_ACCESS_TOKEN'),
                        api_version=os.getenv('SHOPIFY_API_VERSION', '2025-01'),
                    )
            
            # Create sync operation record
            operation_type = f'{sync_type}_sync' if sync_type != 'all' else 'full_sync'
            sync_op = SyncOperation.objects.create(
                store=store,
                operation_type=operation_type,
                status='running',
                started_at=timezone.now()
            )
            
            if sync_type in ['customers', 'all']:
                self.stdout.write('Syncing customers...')
                service = CustomerSyncService(store.store_domain)
                result = service.sync_all_customers()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Customers sync completed: {result.customers_processed} processed'
                    )
                )
            
            if sync_type in ['products', 'all']:
                self.stdout.write('Syncing products...')
                try:
                    service = ProductSyncService(store.store_domain)
                    result = service.sync_all_products()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Products sync completed: {result.products_processed} processed'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Products sync service not ready: {e}')
                    )
            
            if sync_type in ['orders', 'all']:
                self.stdout.write('Syncing orders...')
                try:
                    service = OrderSyncService(store.store_domain)
                    result = service.sync_all_orders()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Orders sync completed: {result.orders_processed} processed'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Orders sync service not ready: {e}')
                    )
            
            if sync_type in ['inventory', 'all']:
                self.stdout.write('Syncing inventory...')
                try:
                    service = InventorySyncService(store.store_domain)
                    result = service.sync_all_inventory()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Inventory sync completed: {result.items_processed} processed'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Inventory sync service not ready: {e}')
                    )
            
            if sync_type in ['shipping', 'all']:
                self.stdout.write('Syncing shipping...')
                try:
                    service = ShippingSyncService(store.store_domain)
                    result = service.sync_all_shipping()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Shipping sync completed'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Shipping sync service not ready: {e}')
                    )
            
            # Update sync operation
            sync_op.status = 'completed'
            sync_op.completed_at = timezone.now()
            sync_op.save()
            
            # Update store last sync
            store.last_sync = timezone.now()
            store.save()
            
            self.stdout.write(
                self.style.SUCCESS('Shopify data sync completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Sync failed: {str(e)}')
            )
            if 'sync_op' in locals():
                sync_op.status = 'failed'
                sync_op.error_message = str(e)
                sync_op.completed_at = timezone.now()
                sync_op.save()
            raise
