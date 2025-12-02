import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.shopify_sync_service import ShopifyShippingSyncService
from core.shopify_client import get_shopify_client

client = get_shopify_client()
sync_service = ShopifyShippingSyncService(
    shop_domain='7fa66c-ac.myshopify.com',
    access_token=client.access_token
)

result = sync_service.sync_shipping_rates()
print(f"\nRate Sync Results:")
print(f"  Rates synced: {result['rates_synced']}")
print(f"  Rates created: {result['rates_created']}")
print(f"  Rates updated: {result['rates_updated']}")
print(f"  Methods processed: {result['methods_processed']}")
print(f"  Errors: {result['errors']}")
