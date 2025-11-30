"""
Test script to verify Shopify ShippingRate object format
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shipping.shopify_shipping_service import ShopifyCarrierServiceWebhook
import json


def test_shipping_rate_format():
    """Test that shipping rates match Shopify's ShippingRate object structure"""
    
    # Sample Shopify rate request
    rate_request = {
        'rate': {
            'origin': {
                'country': 'US',
                'postal_code': '10001',
                'province': 'NY',
                'city': 'New York',
                'address1': '123 Main St',
                'address2': '',
                'address3': None,
                'name': None
            },
            'destination': {
                'country': 'CA',
                'postal_code': 'M5H2N2',
                'province': 'ON',
                'city': 'Toronto',
                'address1': '456 Queen St',
                'address2': '',
                'address3': None,
                'name': 'Test Customer'
            },
            'items': [{
                'name': 'Test Product',
                'sku': 'TEST-123',
                'quantity': 2,
                'grams': 1500,
                'price': 4999,
                'vendor': 'Test Vendor',
                'requires_shipping': True,
                'taxable': True,
                'fulfillment_service': 'manual',
                'properties': None,
                'product_id': 123456,
                'variant_id': 789012
            }],
            'currency': 'CAD',
            'locale': 'en-CA'
        }
    }
    
    # Get rates
    result = ShopifyCarrierServiceWebhook.handle_rate_request(rate_request)
    
    print("=" * 80)
    print("SHOPIFY SHIPPINGRATE OBJECT FORMAT TEST")
    print("=" * 80)
    print()
    print(json.dumps(result, indent=2))
    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    
    # Validate ShippingRate object structure
    if 'rates' not in result:
        print("❌ FAILED: 'rates' key missing")
        return False
    
    rates = result['rates']
    
    if not rates:
        print("⚠️  WARNING: No rates returned")
        return True
    
    for i, rate in enumerate(rates, 1):
        print(f"\n✓ Rate {i}: {rate.get('title', 'N/A')}")
        
        # Check required fields per Shopify ShippingRate object
        required_fields = ['handle', 'title', 'price']
        
        for field in required_fields:
            if field not in rate:
                print(f"  ❌ FAILED: Missing required field '{field}'")
                return False
            else:
                print(f"  ✓ {field}: {rate[field]}")
        
        # Validate price structure (MoneyV2)
        price = rate.get('price', {})
        if not isinstance(price, dict):
            print(f"  ❌ FAILED: 'price' must be a MoneyV2 object (dict)")
            return False
        
        if 'amount' not in price:
            print(f"  ❌ FAILED: 'price.amount' missing")
            return False
        
        if 'currencyCode' not in price:
            print(f"  ❌ FAILED: 'price.currencyCode' missing")
            return False
        
        print(f"  ✓ price.amount: {price['amount']}")
        print(f"  ✓ price.currencyCode: {price['currencyCode']}")
        
        # Optional fields
        optional_fields = ['description', 'min_delivery_date', 'max_delivery_date', 'phone_required']
        for field in optional_fields:
            if field in rate:
                print(f"  ✓ {field}: {rate[field]}")
    
    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED - ShippingRate object format is correct!")
    print("=" * 80)
    return True


if __name__ == '__main__':
    try:
        success = test_shipping_rate_format()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
