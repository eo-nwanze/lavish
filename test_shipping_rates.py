#!/usr/bin/env python
"""
Test Shipping Rate Calculator
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'lavish_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.shopify_shipping_service import ShopifyShippingRateCalculator
import json

# Sample rate request
rate_request = {
    'rate': {
        'origin': {
            'country': 'US',
            'postal_code': '10001',
            'province': 'NY',
            'city': 'New York',
            'name': None,
            'address1': '123 Main St',
            'address2': '',
            'address3': None
        },
        'destination': {
            'country': 'US',
            'postal_code': '90210',
            'province': 'CA',
            'city': 'Beverly Hills',
            'name': 'Test Customer',
            'address1': '456 Oak Ave',
            'address2': '',
            'address3': None
        },
        'items': [
            {
                'name': 'Test Product',
                'sku': 'TEST-123',
                'quantity': 1,
                'grams': 1000,
                'price': 2999,
                'vendor': 'Test Vendor',
                'requires_shipping': True,
                'taxable': True,
                'fulfillment_service': 'manual',
                'properties': None,
                'product_id': 123456,
                'variant_id': 789012
            }
        ],
        'currency': 'USD',
        'locale': 'en-US'
    }
}

print("=" * 80)
print("TESTING SHIPPING RATE CALCULATOR")
print("=" * 80)
print()

print("TEST 1: US to US Shipping")
print("-" * 80)
calculator = ShopifyShippingRateCalculator()
rates = calculator.calculate_rates(rate_request)
print(json.dumps(rates, indent=2))
print()

print("TEST 2: US to Canada (Multi-Currency)")
print("-" * 80)
rate_request['rate']['destination']['country'] = 'CA'
rate_request['rate']['destination']['postal_code'] = 'M5H 2N2'
rate_request['rate']['destination']['province'] = 'ON'
rate_request['rate']['destination']['city'] = 'Toronto'
rate_request['rate']['currency'] = 'CAD'
rate_request['rate']['locale'] = 'en-CA'

rates = calculator.calculate_rates(rate_request)
print(json.dumps(rates, indent=2))
print()

print("TEST 3: US to UK (GBP)")
print("-" * 80)
rate_request['rate']['destination']['country'] = 'GB'
rate_request['rate']['destination']['postal_code'] = 'SW1A 1AA'
rate_request['rate']['destination']['province'] = ''
rate_request['rate']['destination']['city'] = 'London'
rate_request['rate']['currency'] = 'GBP'
rate_request['rate']['locale'] = 'en-GB'

rates = calculator.calculate_rates(rate_request)
print(json.dumps(rates, indent=2))
print()

print("TEST 4: US to Australia (AUD)")
print("-" * 80)
rate_request['rate']['destination']['country'] = 'AU'
rate_request['rate']['destination']['postal_code'] = '2000'
rate_request['rate']['destination']['province'] = 'NSW'
rate_request['rate']['destination']['city'] = 'Sydney'
rate_request['rate']['currency'] = 'AUD'
rate_request['rate']['locale'] = 'en-AU'

rates = calculator.calculate_rates(rate_request)
print(json.dumps(rates, indent=2))
print()

print("=" * 80)
print("ALL TESTS COMPLETE")
print("=" * 80)
