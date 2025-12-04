import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.models import ShopifyCarrierService

carriers = ShopifyCarrierService.objects.filter(active=True)
print(f'Total active carriers: {carriers.count()}\n')

for carrier in carriers:
    print(f'Carrier: {carrier.name}')
    print(f'  Type: {carrier.carrier_service_type}')
    print(f'  Service Discovery: {carrier.service_discovery}')
    print(f'  Callback URL: {carrier.callback_url}')
    print(f'  Active: {carrier.active}')
    print()
