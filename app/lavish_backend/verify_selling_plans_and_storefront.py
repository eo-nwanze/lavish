"""
Verify Selling Plans and Research Storefront Integration
=========================================================

This script will:
1. Query Shopify for all selling plans
2. Compare with Django database
3. Check which products have selling plans
4. Research storefront integration options
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customer_subscriptions.models import SellingPlan, CustomerSubscription
from products.models import ShopifyProduct
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def query_shopify_selling_plans():
    """Query all selling plans from Shopify"""
    
    print("=" * 80)
    print("QUERYING SHOPIFY SELLING PLANS")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    query = """
    query {
      sellingPlanGroups(first: 10) {
        edges {
          node {
            id
            name
            description
            merchantCode
            appId
            options
            createdAt
            sellingPlans(first: 10) {
              edges {
                node {
                  id
                  name
                  description
                  options
                  position
                  billingPolicy {
                    ... on SellingPlanRecurringBillingPolicy {
                      interval
                      intervalCount
                      minCycles
                      maxCycles
                    }
                  }
                  deliveryPolicy {
                    ... on SellingPlanRecurringDeliveryPolicy {
                      interval
                      intervalCount
                    }
                  }
                  pricingPolicies {
                    ... on SellingPlanFixedPricingPolicy {
                      adjustmentType
                      adjustmentValue {
                        ... on SellingPlanPricingPolicyPercentageValue {
                          percentage
                        }
                        ... on MoneyV2 {
                          amount
                          currencyCode
                        }
                      }
                    }
                  }
                }
              }
            }
            productVariants(first: 20) {
              edges {
                node {
                  id
                  title
                  product {
                    id
                    title
                  }
                }
              }
            }
            products(first: 20) {
              edges {
                node {
                  id
                  title
                  status
                }
              }
            }
          }
        }
      }
    }
    """
    
    result = client.execute_graphql_query(query)
    
    if "errors" in result:
        print("\n❌ Error querying Shopify:")
        print(json.dumps(result["errors"], indent=2))
        return None
    
    selling_plan_groups = result.get("data", {}).get("sellingPlanGroups", {}).get("edges", [])
    
    print(f"\n📊 Found {len(selling_plan_groups)} selling plan group(s) in Shopify\n")
    
    shopify_plans = []
    
    for group_edge in selling_plan_groups:
        group = group_edge.get("node", {})
        
        print(f"\n{'='*80}")
        print(f"Selling Plan Group: {group.get('name')}")
        print(f"{'='*80}")
        print(f"ID: {group.get('id')}")
        print(f"Description: {group.get('description', 'N/A')}")
        print(f"Merchant Code: {group.get('merchantCode', 'N/A')}")
        print(f"App ID: {group.get('appId', 'N/A')}")
        print(f"Created: {group.get('createdAt')}")
        
        plans = group.get("sellingPlans", {}).get("edges", [])
        print(f"\nSelling Plans in this group: {len(plans)}")
        
        for plan_edge in plans:
            plan = plan_edge.get("node", {})
            
            print(f"\n  Plan: {plan.get('name')}")
            print(f"  ID: {plan.get('id')}")
            print(f"  Description: {plan.get('description', 'N/A')}")
            
            # Billing Policy
            billing = plan.get("billingPolicy", {})
            print(f"\n  Billing Policy:")
            print(f"    Interval: Every {billing.get('intervalCount', 1)} {billing.get('interval', 'N/A').lower()}")
            print(f"    Min Cycles: {billing.get('minCycles', 'N/A')}")
            print(f"    Max Cycles: {billing.get('maxCycles', 'Unlimited')}")
            
            # Delivery Policy
            delivery = plan.get("deliveryPolicy", {})
            print(f"\n  Delivery Policy:")
            print(f"    Interval: Every {delivery.get('intervalCount', 1)} {delivery.get('interval', 'N/A').lower()}")
            
            # Pricing Policies
            pricing_policies = plan.get("pricingPolicies", [])
            print(f"\n  Pricing Policies: {len(pricing_policies)}")
            for pricing in pricing_policies:
                adjustment_type = pricing.get("adjustmentType", "N/A")
                adjustment_value = pricing.get("adjustmentValue", {})
                
                if "percentage" in adjustment_value:
                    print(f"    {adjustment_type}: {adjustment_value.get('percentage')}% off")
                elif "amount" in adjustment_value:
                    print(f"    {adjustment_type}: ${adjustment_value.get('amount')} {adjustment_value.get('currencyCode')} off")
            
            shopify_plans.append({
                "id": plan.get("id"),
                "name": plan.get("name"),
                "group_id": group.get("id"),
                "group_name": group.get("name")
            })
        
        # Products with this selling plan
        products = group.get("products", {}).get("edges", [])
        print(f"\n  Products with this selling plan: {len(products)}")
        for prod_edge in products:
            prod = prod_edge.get("node", {})
            print(f"    - {prod.get('title')} (Status: {prod.get('status')})")
        
        # Product Variants with this selling plan
        variants = group.get("productVariants", {}).get("edges", [])
        print(f"\n  Product Variants with this selling plan: {len(variants)}")
        for var_edge in variants:
            var = var_edge.get("node", {})
            product = var.get("product", {})
            print(f"    - {product.get('title')} - {var.get('title')}")
    
    return shopify_plans


def compare_with_django():
    """Compare Shopify selling plans with Django database"""
    
    print("\n" + "=" * 80)
    print("COMPARING WITH DJANGO DATABASE")
    print("=" * 80)
    
    # Get Django selling plans
    django_plans = SellingPlan.objects.all()
    
    print(f"\n📊 Django Database:")
    print(f"   Selling Plans: {django_plans.count()}")
    
    if django_plans.exists():
        print("\n   Details:")
        for plan in django_plans:
            print(f"\n   Plan: {plan.name}")
            print(f"   - Shopify ID: {plan.shopify_id}")
            print(f"   - Billing: Every {plan.billing_interval_count} {plan.billing_interval}")
            print(f"   - Delivery: Every {plan.delivery_interval_count} {plan.delivery_interval}")
            print(f"   - Pricing: {plan.price_adjustment_type}")
            
            if plan.price_adjustment_type == 'PERCENTAGE':
                print(f"   - Discount: {plan.price_adjustment_value}% off")
            elif plan.price_adjustment_type == 'FIXED_AMOUNT':
                print(f"   - Discount: ${plan.price_adjustment_value} off")
            
            print(f"   - Needs Push: {plan.needs_shopify_push}")
            print(f"   - Created in Django: {plan.created_in_django}")
    
    # Get Django subscriptions
    subscriptions = CustomerSubscription.objects.all()
    print(f"\n   Customer Subscriptions: {subscriptions.count()}")
    
    if subscriptions.exists():
        print("\n   Details:")
        for sub in subscriptions:
            print(f"\n   Subscription #{sub.id}")
            print(f"   - Customer: {sub.customer}")
            print(f"   - Selling Plan: {sub.selling_plan.name if sub.selling_plan else 'N/A'}")
            print(f"   - Status: {sub.status}")
            print(f"   - Next Billing: {sub.next_billing_date}")
            print(f"   - Shopify Contract ID: {sub.shopify_id or 'Not synced'}")


def check_products_with_selling_plans():
    """Check which Django products should have selling plans"""
    
    print("\n" + "=" * 80)
    print("CHECKING PRODUCTS FOR SELLING PLAN ASSOCIATION")
    print("=" * 80)
    
    # Check if any products are linked to selling plans in Django
    # Note: The relationship might be through a separate model or JSON field
    
    products = ShopifyProduct.objects.all()
    print(f"\n📊 Total Products in Django: {products.count()}")
    
    # Check if products have any subscription-related fields
    subscription_products = products.filter(
        product_type__icontains='subscription'
    ) | products.filter(
        title__icontains='subscription'
    )
    
    print(f"   Products with 'subscription' in name/type: {subscription_products.count()}")
    
    if subscription_products.exists():
        print("\n   Potential subscription products:")
        for prod in subscription_products:
            print(f"   - {prod.title} (Type: {prod.product_type})")
            print(f"     Shopify ID: {prod.shopify_id}")


def research_storefront_integration():
    """Research how to enable subscriptions on Shopify storefront"""
    
    print("\n" + "=" * 80)
    print("STOREFRONT INTEGRATION RESEARCH")
    print("=" * 80)
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SHOPIFY SUBSCRIPTION STOREFRONT INTEGRATION                ║
╚══════════════════════════════════════════════════════════════════════════════╝

To make subscriptions available on your Shopify storefront, you need:

1. SELLING PLAN GROUPS & PRODUCTS
   ─────────────────────────────────
   ✅ Create Selling Plans (done via Django or Shopify Admin)
   ✅ Associate Selling Plans with Products/Variants
   ✅ Products must be ACTIVE and available for purchase

2. SHOPIFY THEME INTEGRATION
   ──────────────────────────
   Your theme needs to support subscription purchase options:
   
   a) OPTION 1: Use Shopify's Built-in Subscription App UI Components
      - Shopify provides liquid tags for rendering subscription options
      - Example: {{ product.selling_plan_groups }}
      
   b) OPTION 2: Custom Implementation
      - Build custom UI using Shopify Ajax API
      - Use theme customization to add subscription selectors

3. REQUIRED SHOPIFY LIQUID CODE
   ─────────────────────────────────
   In your product template (product.liquid or sections/product-template.liquid):
   
   {% if product.selling_plan_groups.size > 0 %}
     <div class="subscription-options">
       {% for group in product.selling_plan_groups %}
         <h3>{{ group.name }}</h3>
         {% for plan in group.selling_plans %}
           <label>
             <input type="radio" 
                    name="selling_plan" 
                    value="{{ plan.id }}"
                    data-selling-plan-id="{{ plan.id }}">
             {{ plan.name }} - {{ plan.price_adjustments[0].value }}% off
           </label>
         {% endfor %}
       {% endfor %}
     </div>
   {% endif %}

4. ADD TO CART WITH SUBSCRIPTION
   ────────────────────────────────
   When adding to cart, include selling_plan parameter:
   
   fetch('/cart/add.js', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       id: variantId,
       quantity: 1,
       selling_plan: selectedSellingPlanId  // <-- Key part!
     })
   });

5. CHECKOUT & PAYMENT
   ────────────────────
   ✅ Shopify handles ALL payment processing automatically
   ✅ Customer payment method is stored by Shopify (PCI compliant)
   ✅ Recurring charges are processed by Shopify
   ✅ Your app receives webhooks for billing events

6. REQUIRED SHOPIFY APP SCOPES
   ────────────────────────────
   Your app needs these scopes (already documented):
   - read_products, write_products
   - read_own_subscription_contracts, write_own_subscription_contracts
   - read_customer_payment_methods (read-only, Shopify manages)

7. HOW IT WORKS - CUSTOMER FLOW
   ──────────────────────────────
   
   Customer Side:
   ──────────────
   1. Customer visits product page
   2. Sees subscription options (if product has selling plans)
   3. Selects "Subscribe & Save" option
   4. Adds to cart with selling_plan parameter
   5. Goes to checkout
   6. Shopify checkout handles payment method
   7. Order is created WITH subscription contract
   
   Backend Side (Django):
   ─────────────────────
   1. Webhook: orders/create → You receive order data
   2. Webhook: subscription_contracts/create → You receive contract
   3. Store contract in CustomerSubscription model
   4. Webhook: subscription_billing_attempts/success → Track billing
   5. Update subscription status in Django

8. PAYMENT PROCESSING
   ───────────────────
   ✅ Shopify Payment Gateway handles ALL payments
   ✅ Customer payment method is tokenized by Shopify
   ✅ Recurring charges are automated by Shopify
   ✅ You DON'T handle payment processing
   ✅ You DO receive webhooks for billing events

9. WHAT YOU NEED TO DO NOW
   ────────────────────────
   
   Step 1: Associate Selling Plans with Products
   ──────────────────────────────────────────────
   - In Shopify Admin or via API
   - Add selling plan groups to your products
   
   Step 2: Update Shopify Theme
   ─────────────────────────────
   - Add subscription option UI to product pages
   - Modify add-to-cart to include selling_plan
   
   Step 3: Test the Flow
   ──────────────────────
   - Make a test purchase with subscription
   - Verify webhook reception
   - Verify Django records creation

10. CHECKING CURRENT STATE
    ──────────────────────
    Run queries to see:
    - Which products have selling plans in Shopify
    - Which selling plans exist
    - If theme supports subscriptions
    """)


def main():
    """Main execution"""
    
    # 1. Query Shopify selling plans
    shopify_plans = query_shopify_selling_plans()
    
    # 2. Compare with Django
    compare_with_django()
    
    # 3. Check products
    check_products_with_selling_plans()
    
    # 4. Research storefront integration
    research_storefront_integration()
    
    print("\n" + "=" * 80)
    print("SUMMARY & NEXT STEPS")
    print("=" * 80)
    
    print("""
    CURRENT STATE:
    ─────────────
    ✅ Django has selling plan models
    ✅ Django can create/update selling plans in Shopify
    ✅ Webhook handlers are implemented
    
    TO ENABLE CUSTOMER SUBSCRIPTIONS ON STOREFRONT:
    ───────────────────────────────────────────────
    
    1. Associate selling plans with products in Shopify
       - Via Shopify Admin OR
       - Via GraphQL API (sellingPlanGroupAddProducts mutation)
    
    2. Update your Shopify theme to show subscription options
       - Add liquid code to product template
       - Modify add-to-cart JavaScript
    
    3. Test subscription purchase flow
       - Customer can select subscription
       - Shopify processes payment
       - Django receives webhooks
    
    DOCUMENTATION TO REVIEW:
    ────────────────────────
    - SUBSCRIPTION_COMPLETE_IMPLEMENTATION_GUIDE.md
    - SHOPIFY_SUBSCRIPTION_PAYMENTS_GUIDE.md
    - SUBSCRIPTION_CONTRACTS_PAYMENT_METHODS_FINDINGS.md
    """)


if __name__ == '__main__':
    main()

