import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.models import ShopifyDeliveryMethod, ShopifyCarrierService
import json

# Check one method in detail
method = ShopifyDeliveryMethod.objects.first()
print(f'Method: {method.name}')
print(f'Zone: {method.zone.name}')
print(f'Profile: {method.zone.profile.name}')
print(f'Type: {method.method_type}')
print(f'Shopify ID: {method.shopify_id}')
print()

# Check carriers
print('Available carriers:')
for carrier in ShopifyCarrierService.objects.all():
    print(f'  - {carrier.name} (Type: {carrier.carrier_service_type})')
