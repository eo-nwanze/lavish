import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.models import ShippingRate

# Check rates for the named carriers
print('Rates for australia_post_mypost_business method:')
rates = ShippingRate.objects.filter(title__icontains='australia_post')
print(f'Found: {rates.count()} rates')
for rate in rates[:5]:
    carrier_name = rate.carrier.name if rate.carrier else 'None'
    print(f'  - {rate.title} | Carrier: {carrier_name}')

print('\nRates for sendle method:')
rates = ShippingRate.objects.filter(title__icontains='sendle')
print(f'Found: {rates.count()} rates')
for rate in rates[:5]:
    carrier_name = rate.carrier.name if rate.carrier else 'None'
    print(f'  - {rate.title} | Carrier: {carrier_name}')

print('\nRates for Express/Standard methods:')
rates = ShippingRate.objects.filter(title__in=['Express', 'Standard'])
print(f'Found: {rates.count()} rates')
for rate in rates[:5]:
    carrier_name = rate.carrier.name if rate.carrier else 'None'
    print(f'  - {rate.title} | Carrier: {carrier_name}')
