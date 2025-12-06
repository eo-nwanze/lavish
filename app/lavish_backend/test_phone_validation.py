"""
Test phone number validation for Shopify
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customers.customer_bidirectional_sync import CustomerBidirectionalSync

def test_phone_validation():
    """Test phone number validation"""
    
    print("\n" + "="*80)
    print("📞 TESTING PHONE NUMBER VALIDATION")
    print("="*80 + "\n")
    
    sync = CustomerBidirectionalSync()
    
    test_cases = [
        ("+61400000000", "+61400000000", "✅ Valid E.164 format"),
        ("+61 400 000 000", "+61400000000", "✅ E.164 with spaces"),
        ("0400000000", "+61400000000", "✅ Australian mobile without +61"),
        ("400000000", "+61400000000", "✅ Australian mobile without 0 or +61"),
        ("+1 (555) 123-4567", "+15551234567", "✅ US format with separators"),
        ("1234567", "", "❌ Too short - invalid"),
        ("", "", "❌ Empty"),
        ("not-a-phone", "", "❌ Invalid format"),
    ]
    
    for input_phone, expected, description in test_cases:
        result = sync.validate_phone_number(input_phone)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: '{input_phone}'")
        print(f"   Expected: '{expected}'")
        print(f"   Got: '{result}'")
        print(f"   {description}")
        print()
    
    print("="*80)
    print("✅ PHONE VALIDATION TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_phone_validation()
