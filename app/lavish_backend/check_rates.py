import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.models import ShippingRate

total = ShippingRate.objects.count()
print(f'Total rates synced: {total}')
print('\nSample rates:')
for rate in ShippingRate.objects.all()[:10]:
    print(f'  {rate}')
