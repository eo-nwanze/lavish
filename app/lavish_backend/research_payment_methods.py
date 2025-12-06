"""
Research Shopify Customer Payment Methods API
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

def research_payment_methods():
    """Check if Shopify API provides customer payment methods"""
    
    print("\n" + "="*80)
    print("🔍 RESEARCHING CUSTOMER PAYMENT METHODS IN SHOPIFY API")
    print("="*80 + "\n")
    
    client = EnhancedShopifyAPIClient()
    
    # Test 1: Check customer schema for payment methods
    print("📋 Test 1: Query customer with payment instruments...")
    print("-"*80)
    
    customer_query = """
    query {
      customers(first: 1) {
        edges {
          node {
            id
            email
            firstName
            lastName
            # Try to get payment methods
            paymentMethods(first: 5) {
              edges {
                node {
                  id
                  instrument {
                    ... on CustomerCreditCard {
                      brand
                      lastDigits
                      expiryMonth
                      expiryYear
                      name
                    }
                    ... on CustomerPaypalBillingAgreement {
                      paypalAccountEmail
                    }
                    ... on CustomerShopPayAgreement {
                      lastDigits
                    }
                  }
                  revokedAt
                  revokedReason
                  subscriptionContracts(first: 1) {
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    result1 = client.execute_graphql_query(customer_query, {})
    print("Response:")
    print(json.dumps(result1, indent=2))
    print()
    
    # Test 2: Check if we can query payment methods directly
    print("\n📋 Test 2: Schema introspection for payment-related types...")
    print("-"*80)
    
    schema_query = """
    query {
      __type(name: "Customer") {
        fields {
          name
          description
          type {
            name
            kind
          }
        }
      }
    }
    """
    
    result2 = client.execute_graphql_query(schema_query, {})
    
    # Filter for payment-related fields
    if result2.get("data", {}).get("__type", {}).get("fields"):
        payment_fields = [
            f for f in result2["data"]["__type"]["fields"] 
            if "payment" in f["name"].lower()
        ]
        
        print("Payment-related fields found:")
        for field in payment_fields:
            print(f"   - {field['name']}: {field.get('description', 'No description')}")
    
    print()
    
    # Test 3: Check subscription contracts (alternative way to get payment info)
    print("\n📋 Test 3: Check subscription contracts for payment info...")
    print("-"*80)
    
    subscription_query = """
    query {
      subscriptionContracts(first: 1) {
        edges {
          node {
            id
            status
            customer {
              id
              email
            }
            customerPaymentMethod {
              id
              instrument {
                ... on CustomerCreditCard {
                  brand
                  lastDigits
                  expiryMonth
                  expiryYear
                }
              }
            }
          }
        }
      }
    }
    """
    
    result3 = client.execute_graphql_query(subscription_query, {})
    print("Response:")
    print(json.dumps(result3, indent=2))
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print("""
Customer payment methods in Shopify:

1. STORED PAYMENT METHODS (paymentMethods):
   - Available via Customer.paymentMethods field
   - Includes credit cards, PayPal, Shop Pay
   - Only shows STORED payment instruments
   - Associated with subscription contracts
   
2. LIMITATIONS:
   - One-time order payments are NOT stored
   - Payment info is tied to subscriptions/recurring billing
   - For security, full card details are never exposed
   - Only last 4 digits and expiry available
   
3. ALTERNATIVE: Order Payment Details
   - Order.transactions field has payment gateway info
   - Doesn't show saved payment methods
   - Shows what was used for that specific order

RECOMMENDATION:
- Pull paymentMethods for subscription customers
- For order-specific payments, use Order.transactions
- Cannot get "all payment methods ever used" by a customer
    """)

if __name__ == "__main__":
    research_payment_methods()
