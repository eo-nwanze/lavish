import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.models import ShopifyDeliveryMethod, ShippingRate

print('Sample delivery methods:')
for method in ShopifyDeliveryMethod.objects.all()[:20]:
    print(f'  - {method.name}')
    
print('\nSample rates with carriers:')
for rate in ShippingRate.objects.all()[:20]:
    carrier_name = rate.carrier.name if rate.carrier else 'None'
    print(f'  - {rate.title} | Carrier: {carrier_name}')
