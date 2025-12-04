import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.models import ShopifyDeliveryMethod
import json

methods = ShopifyDeliveryMethod.objects.all()[:10]
print(f'Total delivery methods: {ShopifyDeliveryMethod.objects.count()}\n')

for method in methods:
    print(f'Method: {method.name}')
    print(f'  Zone: {method.zone.name}')
    print(f'  Profile: {method.zone.profile.name}')
    print(f'  Type: {method.method_type}')
    print(f'  Data: {json.dumps(method.data, indent=4) if method.data else "None"}')
    print()
