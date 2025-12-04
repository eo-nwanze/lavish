#!/usr/bin/env python
"""
Test script to check currency-location sync functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
django.setup()

from locations.models import Country
from locations.shopify_currency_service import ShopifyCurrencyService, LocaleMiddleware
from locations.context_processors import currency_context
from orders.models import ShopifyOrder
from customers.models import ShopifyCustomer
from customer_subscriptions.models import CustomerSubscription

def test_currency_location_sync():
    """Test currency and location data synchronization"""
    
    print('🔍 Testing Currency-Location Sync Functionality')
    print('=' * 50)
    
    # Test 1: Country-Currency Mapping
    print('\n📊 Test 1: Country-Currency Mapping')
    test_countries = ['Australia', 'United States', 'United Kingdom', 'Canada', 'Germany']
    
    for country_name in test_countries:
        country = Country.objects.filter(name=country_name).first()
        if country:
            print(f'  {country.name}: {country.currency} -> {country.currency_symbol}')
        else:
            print(f'  {country_name}: Not found in database')
    
    # Test 2: LocaleMiddleware Mapping
    print('\n📊 Test 2: LocaleMiddleware Country-to-Currency Mapping')
    
    class MockResponse:
        pass
    
    middleware = LocaleMiddleware(lambda req: MockResponse())
    test_country_codes = ['AU', 'US', 'GB', 'CA', 'DE']
    
    for country_code in test_country_codes:
        currency = middleware._country_to_currency(country_code)
        print(f'  {country_code} -> {currency}')
    
    # Test 3: Currency Conversion
    print('\n📊 Test 3: Currency Conversion')
    service = ShopifyCurrencyService('test-shop.myshopify.com', 'test-token')
    
    test_conversions = [
        (10.00, 'USD', 'AUD'),
        (10.00, 'AUD', 'USD'),
        (10.00, 'GBP', 'EUR'),
        (10.00, 'EUR', 'GBP'),
    ]
    
    for amount, from_curr, to_curr in test_conversions:
        converted = service.convert_currency(amount, from_curr, to_curr)
        print(f'  {amount} {from_curr} -> {converted} {to_curr}')
    
    # Test 4: Currency Formatting
    print('\n📊 Test 4: Currency Formatting')
    test_formats = [
        (10.50, 'AUD', 'en_AU'),
        (10.50, 'USD', 'en_US'),
        (10.50, 'GBP', 'en_GB'),
        (10.50, 'EUR', 'fr_FR'),
        (10.50, 'EUR', 'de_DE'),
    ]
    
    for amount, currency, locale in test_formats:
        formatted = service.format_price(amount, currency, locale)
        print(f'  {amount} {currency} ({locale}) -> {formatted}')
    
    # Test 5: Context Processor
    print('\n📊 Test 5: Context Processor Data')
    
    class MockRequest:
        def __init__(self):
            self.currency = 'AUD'
            self.country = 'AU'
            self.LANGUAGE_CODE = 'en'
    
    mock_request = MockRequest()
    context = currency_context(mock_request)
    
    print(f'  Current currency: {context["current_currency"]}')
    print(f'  Currency symbol: {context["currency_symbol"]}')
    print(f'  Supported currencies: {context["supported_currencies"]}')
    
    # Test 6: Real Data Analysis
    print('\n📊 Test 6: Real Data Analysis')
    
    # Check countries
    countries = Country.objects.all()
    print(f'  Countries in database: {countries.count()}')
    
    currency_counts = {}
    for country in countries:
        currency = country.currency or 'UNKNOWN'
        currency_counts[currency] = currency_counts.get(currency, 0) + 1
    
    print('  Currency distribution:')
    for currency, count in sorted(currency_counts.items()):
        print(f'    {currency}: {count} countries')
    
    # Check orders
    orders = ShopifyOrder.objects.all()
    print(f'  Orders in database: {orders.count()}')
    
    order_currency_counts = {}
    for order in orders:
        currency = order.currency_code or 'UNKNOWN'
        order_currency_counts[currency] = order_currency_counts.get(currency, 0) + 1
    
    print('  Order currency distribution:')
    for currency, count in sorted(order_currency_counts.items()):
        print(f'    {currency}: {count} orders')
    
    # Check subscriptions
    subscriptions = CustomerSubscription.objects.all()
    print(f'  Subscriptions in database: {subscriptions.count()}')
    
    sub_currency_counts = {}
    for sub in subscriptions:
        currency = sub.currency or 'UNKNOWN'
        sub_currency_counts[currency] = sub_currency_counts.get(currency, 0) + 1
    
    print('  Subscription currency distribution:')
    for currency, count in sorted(sub_currency_counts.items()):
        print(f'    {currency}: {count} subscriptions')
    
    # Test 7: Consistency Check
    print('\n📊 Test 7: Currency-Location Consistency Check')
    
    # Check customer addresses
    customers = ShopifyCustomer.objects.all()[:3]
    for customer in customers:
        print(f'  Customer: {customer.first_name} {customer.last_name}')
        
        if hasattr(customer, 'subscription_address'):
            addr = customer.subscription_address
            if addr and addr.country:
                print(f'    Address country: {addr.country}')
                
                country_obj = Country.objects.filter(name__icontains=addr.country).first()
                if country_obj:
                    print(f'    Location currency: {country_obj.currency}')
                    
                    # Check customer's orders
                    customer_orders = ShopifyOrder.objects.filter(customer=customer)[:1]
                    for order in customer_orders:
                        print(f'    Order currency: {order.currency_code}')
                        
                        if country_obj.currency != order.currency_code:
                            print(f'    ⚠️  MISMATCH detected!')
                        else:
                            print(f'    ✅ Currency matches location')
    
    print('\n🎉 Currency-Location Sync Testing Complete!')
    print('=' * 50)

if __name__ == '__main__':
    test_currency_location_sync()