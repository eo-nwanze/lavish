"""
Subscription Payment Implementation Example
============================================

This script demonstrates how to:
1. Fetch customer payment methods from Shopify
2. Create subscriptions with payment methods
3. Automatically bill subscriptions
4. Handle payment errors
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customer_subscriptions.models import CustomerSubscription, SubscriptionBillingAttempt
from customer_subscriptions.bidirectional_sync import subscription_sync
from customers.models import ShopifyCustomer
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json


class SubscriptionPaymentService:
    """Service for handling subscription payments"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def get_customer_payment_methods(self, customer_shopify_id: str):
        """
        Fetch customer payment methods from Shopify
        
        Args:
            customer_shopify_id: Customer's Shopify GID
            
        Returns:
            List of payment methods
        """
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
                    __typename
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
                      name
                    }
                  }
                  revokedAt
                  revokedReason
                }
              }
            }
          }
        }
        """
        
        variables = {
            "customerId": customer_shopify_id
        }
        
        try:
            result = self.client.execute_graphql_query(query, variables)
            
            if "errors" in result:
                # Check if it's an access denied error
                errors = result["errors"]
                if any("ACCESS_DENIED" in str(e) for e in errors):
                    return {
                        "success": False,
                        "message": "API scope 'read_customer_payment_methods' required. Add in Shopify Partners Dashboard.",
                        "requires_scope": True
                    }
                
                return {
                    "success": False,
                    "message": f"GraphQL errors: {errors}"
                }
            
            customer_data = result.get("data", {}).get("customer", {})
            payment_methods_edges = customer_data.get("paymentMethods", {}).get("edges", [])
            
            payment_methods = []
            for edge in payment_methods_edges:
                pm = edge.get("node", {})
                instrument = pm.get("instrument", {})
                
                # Skip revoked payment methods
                if pm.get("revokedAt"):
                    continue
                
                # Parse based on type
                pm_type = instrument.get("__typename", "Unknown")
                
                payment_method = {
                    "id": pm.get("id"),
                    "type": pm_type,
                    "revoked_at": pm.get("revokedAt"),
                    "revoked_reason": pm.get("revokedReason")
                }
                
                if pm_type == "CustomerCreditCard":
                    payment_method.update({
                        "brand": instrument.get("brand"),
                        "last_digits": instrument.get("lastDigits"),
                        "expiry_month": instrument.get("expiryMonth"),
                        "expiry_year": instrument.get("expiryYear"),
                        "name": instrument.get("name"),
                        "display": f"{instrument.get('brand')} •••• {instrument.get('lastDigits')}"
                    })
                elif pm_type == "CustomerPaypalBillingAgreement":
                    payment_method.update({
                        "paypal_email": instrument.get("paypalAccountEmail"),
                        "display": f"PayPal {instrument.get('paypalAccountEmail')}"
                    })
                elif pm_type == "CustomerShopPayAgreement":
                    payment_method.update({
                        "last_digits": instrument.get("lastDigits"),
                        "name": instrument.get("name"),
                        "display": f"Shop Pay •••• {instrument.get('lastDigits')}"
                    })
                
                payment_methods.append(payment_method)
            
            return {
                "success": True,
                "customer_email": customer_data.get("email"),
                "customer_name": customer_data.get("displayName"),
                "payment_methods": payment_methods,
                "count": len(payment_methods)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Exception: {str(e)}"
            }
    
    def bill_subscription(self, subscription_id: int, origin_time: str = None):
        """
        Bill a subscription (create billing attempt)
        
        Args:
            subscription_id: Django subscription ID
            origin_time: Optional ISO datetime for billing cycle
            
        Returns:
            Billing result
        """
        try:
            subscription = CustomerSubscription.objects.get(id=subscription_id)
        except CustomerSubscription.DoesNotExist:
            return {
                "success": False,
                "message": f"Subscription {subscription_id} not found"
            }
        
        # Check if subscription has payment method
        if not subscription.payment_method_id:
            return {
                "success": False,
                "message": "Subscription has no payment method. Customer must add payment method in Customer Accounts.",
                "requires_payment_method": True,
                "customer_accounts_url": f"https://{subscription.store_domain}/account"
            }
        
        # Create billing attempt
        result = subscription_sync.create_billing_attempt(subscription, origin_time)
        
        if result.get("success"):
            # Update next billing date
            if subscription.next_billing_date:
                interval_map = {
                    'DAY': 'days',
                    'WEEK': 'weeks',
                    'MONTH': 'months',
                    'YEAR': 'years'
                }
                
                interval_type = interval_map.get(subscription.billing_policy_interval, 'months')
                interval_count = subscription.billing_policy_interval_count
                
                # Calculate next billing date
                kwargs = {interval_type: interval_count}
                subscription.next_billing_date = subscription.next_billing_date + relativedelta(**kwargs)
                subscription.billing_cycle_count += 1
                subscription.save()
        
        return result
    
    def bill_all_due_subscriptions(self, dry_run: bool = False):
        """
        Bill all subscriptions due today
        
        Args:
            dry_run: If True, only show what would be billed
            
        Returns:
            Results summary
        """
        today = date.today()
        
        subscriptions_due = CustomerSubscription.objects.filter(
            status='ACTIVE',
            next_billing_date__lte=today
        )
        
        results = {
            "total": subscriptions_due.count(),
            "successful": 0,
            "failed": 0,
            "requires_payment_method": 0,
            "errors": []
        }
        
        print(f"\n{'🔍 DRY RUN:' if dry_run else '💳 BILLING:'} {results['total']} subscriptions due")
        print("=" * 60)
        
        for subscription in subscriptions_due:
            customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}"
            
            print(f"\n📦 Subscription #{subscription.id}: {customer_name}")
            print(f"   Billing Date: {subscription.next_billing_date}")
            print(f"   Amount: ${subscription.total_price} {subscription.currency}")
            
            if dry_run:
                if subscription.payment_method_id:
                    print(f"   ✅ Has payment method")
                else:
                    print(f"   ⚠️  No payment method - would skip")
                continue
            
            # Actually bill
            result = self.bill_subscription(subscription.id)
            
            if result.get("success"):
                results["successful"] += 1
                order_name = result.get("order_name", "pending")
                print(f"   ✅ SUCCESS - Order: {order_name}")
            elif result.get("requires_payment_method"):
                results["requires_payment_method"] += 1
                print(f"   ⚠️  No payment method - skipped")
            else:
                results["failed"] += 1
                print(f"   ❌ FAILED: {result.get('message')}")
                results["errors"].append({
                    "subscription_id": subscription.id,
                    "customer": customer_name,
                    "error": result.get("message")
                })
        
        print("\n" + "=" * 60)
        print(f"✅ Successful: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⚠️  No Payment Method: {results['requires_payment_method']}")
        
        return results


def demo_fetch_payment_methods():
    """Demo: Fetch payment methods for a customer"""
    print("\n" + "=" * 60)
    print("DEMO: Fetch Customer Payment Methods")
    print("=" * 60)
    
    # Get first customer with Shopify ID
    customer = ShopifyCustomer.objects.filter(
        shopify_id__isnull=False
    ).exclude(shopify_id='').first()
    
    if not customer:
        print("❌ No customers with Shopify ID found")
        return
    
    print(f"\n👤 Customer: {customer.full_name} ({customer.email})")
    print(f"   Shopify ID: {customer.shopify_id}")
    
    service = SubscriptionPaymentService()
    result = service.get_customer_payment_methods(customer.shopify_id)
    
    if result.get("requires_scope"):
        print(f"\n⚠️  {result['message']}")
        print("\nTo enable payment method access:")
        print("1. Go to Shopify Partners Dashboard")
        print("2. Edit your app")
        print("3. Add scope: read_customer_payment_methods")
        print("4. Reinstall app to your store")
        return
    
    if not result.get("success"):
        print(f"\n❌ Error: {result.get('message')}")
        return
    
    payment_methods = result.get("payment_methods", [])
    
    print(f"\n💳 Payment Methods: {len(payment_methods)}")
    
    if not payment_methods:
        print("   No payment methods found")
        print("\n   Customer can add payment methods in:")
        print(f"   https://{customer.store_domain}/account")
    else:
        for i, pm in enumerate(payment_methods, 1):
            print(f"\n   {i}. {pm.get('display', 'Unknown')}")
            print(f"      ID: {pm['id']}")
            print(f"      Type: {pm['type']}")
            if pm.get('expiry_month') and pm.get('expiry_year'):
                print(f"      Expires: {pm['expiry_month']}/{pm['expiry_year']}")


def demo_bill_subscription():
    """Demo: Bill a specific subscription"""
    print("\n" + "=" * 60)
    print("DEMO: Bill a Subscription")
    print("=" * 60)
    
    # Get first active subscription
    subscription = CustomerSubscription.objects.filter(
        status='ACTIVE'
    ).first()
    
    if not subscription:
        print("❌ No active subscriptions found")
        return
    
    customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}"
    
    print(f"\n📦 Subscription #{subscription.id}")
    print(f"   Customer: {customer_name}")
    print(f"   Next Billing: {subscription.next_billing_date}")
    print(f"   Amount: ${subscription.total_price} {subscription.currency}")
    print(f"   Payment Method: {subscription.payment_method_id or 'None'}")
    
    if not subscription.payment_method_id:
        print(f"\n⚠️  No payment method!")
        print(f"   Customer must add payment method at:")
        print(f"   https://{subscription.store_domain}/account")
        return
    
    service = SubscriptionPaymentService()
    
    print(f"\n💳 Creating billing attempt...")
    result = service.bill_subscription(subscription.id)
    
    if result.get("success"):
        print(f"\n✅ SUCCESS!")
        print(f"   Billing Attempt ID: {result.get('billing_attempt_id')}")
        print(f"   Order ID: {result.get('order_id')}")
        print(f"   Order Name: {result.get('order_name')}")
        print(f"   Ready: {result.get('ready')}")
        
        if result.get('next_action_url'):
            print(f"\n⚠️  3D Secure Required:")
            print(f"   {result.get('next_action_url')}")
            print(f"   Customer will receive email to complete verification")
    else:
        print(f"\n❌ FAILED: {result.get('message')}")


def demo_bill_all_due():
    """Demo: Bill all due subscriptions (dry run)"""
    service = SubscriptionPaymentService()
    
    print("\n🔍 Running DRY RUN (no actual billing)...")
    service.bill_all_due_subscriptions(dry_run=True)
    
    print("\n" + "=" * 60)
    response = input("\nRun actual billing? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n💳 Running ACTUAL BILLING...")
        service.bill_all_due_subscriptions(dry_run=False)
    else:
        print("\n✅ Skipped actual billing")


def main():
    """Main menu"""
    print("\n" + "=" * 60)
    print("SUBSCRIPTION PAYMENT SERVICE - DEMO")
    print("=" * 60)
    
    print("\n1. Fetch customer payment methods")
    print("2. Bill a specific subscription")
    print("3. Bill all due subscriptions")
    print("4. Run all demos")
    print("5. Exit")
    
    choice = input("\nSelect option (1-5): ")
    
    if choice == '1':
        demo_fetch_payment_methods()
    elif choice == '2':
        demo_bill_subscription()
    elif choice == '3':
        demo_bill_all_due()
    elif choice == '4':
        demo_fetch_payment_methods()
        demo_bill_subscription()
        demo_bill_all_due()
    else:
        print("\n👋 Goodbye!")


if __name__ == '__main__':
    main()

