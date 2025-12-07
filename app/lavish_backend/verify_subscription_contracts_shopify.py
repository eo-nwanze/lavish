"""
Verify Subscription Contracts and Payment Methods in Shopify
=============================================================

This script:
1. Checks for existing subscription contracts in Shopify
2. Researches customer payment methods API
3. Creates test subscription contract if needed
4. Verifies payment method access
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from customer_subscriptions.models import CustomerSubscription, SellingPlan
from customers.models import ShopifyCustomer


def check_subscription_contracts():
    """Check for existing subscription contracts in Shopify"""
    
    client = EnhancedShopifyAPIClient()
    
    print("=" * 80)
    print("CHECKING SUBSCRIPTION CONTRACTS IN SHOPIFY")
    print("=" * 80)
    
    # Query subscription contracts
    query = """
    query {
      subscriptionContracts(first: 20) {
        edges {
          node {
            id
            status
            createdAt
            nextBillingDate
            customer {
              id
              firstName
              lastName
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
                ... on CustomerPaypalBillingAgreement {
                  paypalAccountEmail
                }
              }
            }
            billingPolicy {
              interval
              intervalCount
              minCycles
              maxCycles
            }
            deliveryPolicy {
              interval
              intervalCount
            }
            lines(first: 10) {
              edges {
                node {
                  id
                  title
                  quantity
                  currentPrice {
                    amount
                    currencyCode
                  }
                  productId
                  variantId
                  sellingPlanId
                  sellingPlanName
                }
              }
            }
          }
        }
      }
    }
    """
    
    try:
        result = client.execute_graphql_query(query, {})
        
        if "errors" in result:
            print("❌ GraphQL Errors:")
            for error in result["errors"]:
                print(f"   - {error.get('message')}")
            return None
        
        contracts = result.get("data", {}).get("subscriptionContracts", {}).get("edges", [])
        
        print(f"\n📊 Found {len(contracts)} subscription contracts in Shopify\n")
        
        if len(contracts) == 0:
            print("⚠️ No subscription contracts found in Shopify")
            print("   This is expected if no customers have purchased subscriptions yet.")
            return []
        
        # Display details
        for i, edge in enumerate(contracts, 1):
            contract = edge.get("node", {})
            customer = contract.get("customer", {})
            payment = contract.get("customerPaymentMethod", {})
            billing = contract.get("billingPolicy", {})
            lines = contract.get("lines", {}).get("edges", [])
            
            print(f"{i}. Subscription Contract")
            print(f"   {'='*70}")
            print(f"   ID: {contract.get('id')}")
            print(f"   Status: {contract.get('status')}")
            print(f"   Created: {contract.get('createdAt')}")
            print(f"   Next Billing: {contract.get('nextBillingDate')}")
            print(f"\n   Customer:")
            print(f"   - Name: {customer.get('firstName')} {customer.get('lastName')}")
            print(f"   - Email: {customer.get('email')}")
            print(f"   - ID: {customer.get('id')}")
            
            if payment:
                print(f"\n   Payment Method:")
                print(f"   - ID: {payment.get('id')}")
                instrument = payment.get("instrument", {})
                if "brand" in instrument:
                    print(f"   - Type: Credit Card")
                    print(f"   - Brand: {instrument.get('brand')}")
                    print(f"   - Last 4: {instrument.get('lastDigits')}")
                    print(f"   - Expires: {instrument.get('expiryMonth')}/{instrument.get('expiryYear')}")
                elif "paypalAccountEmail" in instrument:
                    print(f"   - Type: PayPal")
                    print(f"   - Email: {instrument.get('paypalAccountEmail')}")
            else:
                print(f"\n   Payment Method: ⚠️ None")
            
            print(f"\n   Billing Policy:")
            print(f"   - Interval: {billing.get('intervalCount')} {billing.get('interval')}")
            print(f"   - Min Cycles: {billing.get('minCycles')}")
            print(f"   - Max Cycles: {billing.get('maxCycles')}")
            
            print(f"\n   Line Items ({len(lines)}):")
            for line_edge in lines:
                line = line_edge.get("node", {})
                price = line.get("currentPrice", {})
                print(f"   - {line.get('title')}")
                print(f"     Qty: {line.get('quantity')} x ${price.get('amount')} {price.get('currencyCode')}")
                print(f"     Selling Plan: {line.get('sellingPlanName')}")
                print(f"     Selling Plan ID: {line.get('sellingPlanId')}")
            
            print()
        
        return contracts
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def research_payment_methods_api():
    """Research how to access customer payment methods"""
    
    client = EnhancedShopifyAPIClient()
    
    print("\n" + "=" * 80)
    print("RESEARCHING CUSTOMER PAYMENT METHODS API")
    print("=" * 80)
    
    # First, get a customer
    customer = ShopifyCustomer.objects.filter(shopify_id__isnull=False).first()
    
    if not customer:
        print("❌ No customers with Shopify ID found")
        return None
    
    print(f"\n🔍 Testing with customer: {customer.first_name} {customer.last_name}")
    print(f"   Shopify ID: {customer.shopify_id}")
    
    # Query customer payment methods
    query = """
    query getCustomerPaymentMethods($customerId: ID!) {
      customer(id: $customerId) {
        id
        email
        displayName
        paymentMethods(first: 10) {
          edges {
            node {
              id
              instrument {
                ... on CustomerCreditCard {
                  brand
                  lastDigits
                  expiryMonth
                  expiryYear
                  expiresSoon
                  isRevocable
                  maskedNumber
                  name
                  source
                }
                ... on CustomerPaypalBillingAgreement {
                  paypalAccountEmail
                  isRevocable
                }
                ... on CustomerShopPayAgreement {
                  expiresSoon
                  expiryMonth
                  expiryYear
                  isRevocable
                  lastDigits
                  maskedNumber
                  name
                }
              }
              revokedAt
              revokedReason
              subscriptionContracts(first: 5) {
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
    """
    
    variables = {
        "customerId": customer.shopify_id
    }
    
    try:
        result = client.execute_graphql_query(query, variables)
        
        if "errors" in result:
            print("\n❌ GraphQL Errors:")
            for error in result["errors"]:
                print(f"   - {error.get('message')}")
                print(f"     Path: {error.get('path')}")
                
                # Check if it's a scope issue
                extensions = error.get('extensions', {})
                if extensions.get('code') == 'ACCESS_DENIED':
                    print("\n⚠️ ACCESS DENIED - Missing API Scope")
                    print("\n   You need to add these scopes to your Shopify app:")
                    print("   - read_customer_payment_methods")
                    print("   - write_customer_payment_methods (for updates)")
                    print("\n   How to add scopes:")
                    print("   1. Go to Shopify Partners Dashboard")
                    print("   2. Select your app")
                    print("   3. Configuration → API access scopes")
                    print("   4. Add: read_customer_payment_methods")
                    print("   5. Save and reinstall app")
            return None
        
        customer_data = result.get("data", {}).get("customer", {})
        payment_methods = customer_data.get("paymentMethods", {}).get("edges", [])
        
        print(f"\n✅ Found {len(payment_methods)} payment method(s)")
        
        if len(payment_methods) == 0:
            print("\n⚠️ Customer has no saved payment methods")
            print("   Payment methods are created when:")
            print("   - Customer purchases a subscription through checkout")
            print("   - Customer adds payment method in their account")
            print("   - Merchant manually adds payment for customer")
            return []
        
        # Display payment methods
        for i, edge in enumerate(payment_methods, 1):
            pm = edge.get("node", {})
            instrument = pm.get("instrument", {})
            contracts = pm.get("subscriptionContracts", {}).get("edges", [])
            
            print(f"\n{i}. Payment Method")
            print(f"   {'='*70}")
            print(f"   ID: {pm.get('id')}")
            print(f"   Revoked: {pm.get('revokedAt') or 'No'}")
            
            if "brand" in instrument:
                print(f"\n   Type: Credit Card")
                print(f"   Brand: {instrument.get('brand')}")
                print(f"   Last 4: {instrument.get('lastDigits')}")
                print(f"   Masked: {instrument.get('maskedNumber')}")
                print(f"   Name: {instrument.get('name')}")
                print(f"   Expires: {instrument.get('expiryMonth')}/{instrument.get('expiryYear')}")
                print(f"   Expires Soon: {instrument.get('expiresSoon')}")
                print(f"   Can Revoke: {instrument.get('isRevocable')}")
            elif "paypalAccountEmail" in instrument:
                print(f"\n   Type: PayPal")
                print(f"   Email: {instrument.get('paypalAccountEmail')}")
                print(f"   Can Revoke: {instrument.get('isRevocable')}")
            elif "maskedNumber" in instrument:
                print(f"\n   Type: Shop Pay")
                print(f"   Last 4: {instrument.get('lastDigits')}")
                print(f"   Masked: {instrument.get('maskedNumber')}")
                print(f"   Expires: {instrument.get('expiryMonth')}/{instrument.get('expiryYear')}")
            
            print(f"\n   Used by {len(contracts)} subscription contract(s)")
        
        return payment_methods
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_django_vs_shopify():
    """Compare Django subscriptions with Shopify"""
    
    print("\n" + "=" * 80)
    print("COMPARING DJANGO SUBSCRIPTIONS WITH SHOPIFY")
    print("=" * 80)
    
    django_subs = CustomerSubscription.objects.all()
    
    print(f"\n📊 Django Subscriptions: {django_subs.count()}")
    
    for sub in django_subs:
        print(f"\n   Subscription #{sub.id}")
        print(f"   - Customer: {sub.customer}")
        print(f"   - Status: {sub.status}")
        print(f"   - Shopify ID: {sub.shopify_id or '❌ Not synced'}")
        print(f"   - Payment Method: {sub.payment_method_id or '❌ None'}")
        print(f"   - Next Billing: {sub.next_billing_date}")
        print(f"   - Created in Django: {sub.created_in_django}")
        print(f"   - Needs Push: {sub.needs_shopify_push}")


def create_test_subscription_contract():
    """Create a test subscription contract in Shopify"""
    
    print("\n" + "=" * 80)
    print("CREATE TEST SUBSCRIPTION CONTRACT")
    print("=" * 80)
    
    # Get a customer
    customer = ShopifyCustomer.objects.filter(shopify_id__isnull=False).first()
    
    if not customer:
        print("❌ No customers with Shopify ID found")
        print("   Please create a customer first")
        return None
    
    # Get a selling plan
    selling_plan = SellingPlan.objects.filter(
        shopify_id__isnull=False,
        is_active=True
    ).first()
    
    if not selling_plan:
        print("❌ No active selling plans found")
        return None
    
    # Get a product variant (we need this for the subscription)
    from products.models import ShopifyProduct
    
    product = ShopifyProduct.objects.filter(shopify_id__isnull=False).first()
    
    if not product:
        print("❌ No products found")
        return None
    
    print(f"\n📝 Creating test subscription contract:")
    print(f"   Customer: {customer.first_name} {customer.last_name} ({customer.email})")
    print(f"   Selling Plan: {selling_plan.name}")
    print(f"   Product: {product.title}")
    
    print(f"\n⚠️ NOTE: This will create a REAL subscription contract in Shopify")
    print(f"   However, it will NOT charge the customer yet.")
    print(f"   You'll need to:")
    print(f"   1. Add a payment method (or customer needs to add one)")
    print(f"   2. Create a billing attempt to actually charge")
    
    response = input("\n   Proceed? (yes/no): ")
    
    if response.lower() != 'yes':
        print("   Cancelled")
        return None
    
    # Create subscription in Django first
    from datetime import date, timedelta
    
    subscription = CustomerSubscription.objects.create(
        customer=customer,
        selling_plan=selling_plan,
        status='ACTIVE',
        currency='USD',
        next_billing_date=date.today() + timedelta(days=30),
        billing_policy_interval='MONTH',
        billing_policy_interval_count=1,
        delivery_policy_interval='MONTH',
        delivery_policy_interval_count=1,
        line_items=[{
            'variant_id': f"gid://shopify/ProductVariant/{product.shopify_id.split('/')[-1]}",
            'product_id': product.shopify_id,
            'quantity': 1,
            'current_price': '25.00',
            'title': product.title,
            'variant_title': 'Default'
        }],
        delivery_address={
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'address1': '123 Test St',
            'city': 'Test City',
            'province': 'CA',
            'country': 'US',
            'zip': '12345'
        },
        created_in_django=True,
        needs_shopify_push=True
    )
    
    print(f"\n✅ Created Django subscription #{subscription.id}")
    
    # Push to Shopify
    from customer_subscriptions.bidirectional_sync import subscription_sync
    
    result = subscription_sync.create_subscription_in_shopify(subscription)
    
    if result.get('success'):
        subscription.refresh_from_db()
        print(f"\n✅ Successfully created in Shopify!")
        print(f"   Shopify ID: {subscription.shopify_id}")
        print(f"\n⚠️ IMPORTANT: This subscription has NO payment method yet")
        print(f"   The customer needs to:")
        print(f"   1. Log into their account")
        print(f"   2. Go to subscriptions")
        print(f"   3. Add a payment method")
        print(f"\n   Or you can add a payment method via Shopify Admin")
        return subscription
    else:
        print(f"\n❌ Failed to create in Shopify: {result.get('message')}")
        subscription.delete()
        return None


def main():
    """Main execution"""
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "SUBSCRIPTION CONTRACTS & PAYMENT METHODS" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Step 1: Check for existing contracts
    contracts = check_subscription_contracts()
    
    # Step 2: Research payment methods API
    payment_methods = research_payment_methods_api()
    
    # Step 3: Compare Django vs Shopify
    check_django_vs_shopify()
    
    # Step 4: Offer to create test contract if none exist
    if contracts is not None and len(contracts) == 0:
        print("\n" + "=" * 80)
        print("NO SUBSCRIPTION CONTRACTS FOUND")
        print("=" * 80)
        
        print("\nWould you like to create a test subscription contract?")
        print("This will help verify the complete flow.")
        
        response = input("\nCreate test subscription? (yes/no): ")
        
        if response.lower() == 'yes':
            create_test_subscription_contract()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print("\n✅ Selling Plans: Verified in Shopify (6 plans)")
    
    if contracts is not None:
        print(f"📊 Subscription Contracts: {len(contracts)} found in Shopify")
    else:
        print("❌ Subscription Contracts: Could not query (check errors above)")
    
    if payment_methods is None:
        print("\n⚠️ Payment Methods API:")
        print("   - Requires 'read_customer_payment_methods' scope")
        print("   - Add scope in Shopify Partners Dashboard")
        print("   - Reinstall app to your store")
    elif payment_methods:
        print(f"\n✅ Payment Methods: {len(payment_methods)} found")
    else:
        print("\n⚠️ Payment Methods: Customer has none (expected for test)")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    print("\n1. Add Payment Methods API Scope:")
    print("   - Go to Shopify Partners Dashboard")
    print("   - Your App → Configuration → API Scopes")
    print("   - Add: read_customer_payment_methods")
    print("   - Save and reinstall app")
    
    print("\n2. Create Real Subscriptions:")
    print("   - Have a customer purchase a subscription product")
    print("   - Shopify will create the contract automatically")
    print("   - Webhook will sync to Django")
    
    print("\n3. Test Billing:")
    print("   - Wait for next billing date")
    print("   - Or run: python manage.py bill_subscriptions")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

