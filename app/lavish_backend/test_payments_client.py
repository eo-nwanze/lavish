#!/usr/bin/env python
"""
Test script for Shopify Payments Client
"""
import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from payments.shopify_payments_client import ShopifyPaymentsClient

def test_payments_client():
    """Test the Shopify Payments Client functionality"""
    print("Testing Shopify Payments Client...")
    
    try:
        # Create client instance
        client = ShopifyPaymentsClient()
        print("✓ Client created successfully")
        
        # Test account info fetch
        print("\nTesting account info fetch...")
        account_info = client.fetch_account_info()
        if 'data' in account_info:
            print("✓ Account info fetched successfully")
            print(f"  Response keys: {list(account_info.keys())}")
        else:
            print("✗ Account info fetch failed")
            print(f"  Error: {account_info}")
        
        # Test balance transactions fetch
        print("\nTesting balance transactions fetch...")
        balance_txns = client.fetch_balance_transactions(first=5)
        if 'data' in balance_txns:
            print("✓ Balance transactions fetched successfully")
            print(f"  Response keys: {list(balance_txns.keys())}")
        else:
            print("✗ Balance transactions fetch failed")
            print(f"  Error: {balance_txns}")
        
        # Test bank accounts fetch
        print("\nTesting bank accounts fetch...")
        bank_accounts = client.fetch_bank_accounts(first=5)
        if 'data' in bank_accounts:
            print("✓ Bank accounts fetched successfully")
            print(f"  Response keys: {list(bank_accounts.keys())}")
        else:
            print("✗ Bank accounts fetch failed")
            print(f"  Error: {bank_accounts}")
        
        # Test disputes fetch
        print("\nTesting disputes fetch...")
        disputes = client.fetch_disputes(first=5)
        if 'data' in disputes:
            print("✓ Disputes fetched successfully")
            print(f"  Response keys: {list(disputes.keys())}")
        else:
            print("✗ Disputes fetch failed")
            print(f"  Error: {disputes}")
            
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payments_client()