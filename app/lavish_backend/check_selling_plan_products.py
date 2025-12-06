"""
Check if selling plans are tied to actual products on the Shopify store
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customer_subscriptions.models import SellingPlan
from products.models import ShopifyProduct
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

def check_selling_plans_on_shopify():
    """Check if selling plans in Django are properly associated with products on Shopify"""
    
    print("\n" + "="*80)
    print("🔍 CHECKING SELLING PLANS & PRODUCT ASSOCIATIONS")
    print("="*80 + "\n")
    
    # Get all selling plans from Django
    django_plans = SellingPlan.objects.all()
    
    print(f"📊 Found {django_plans.count()} selling plans in Django\n")
    
    if not django_plans.exists():
        print("❌ No selling plans found in Django database")
        print("\n💡 To create selling plans, run:")
        print("   python manage.py create_subscription_packages")
        return
    
    client = EnhancedShopifyAPIClient()
    
    # Display Django plans
    print("📋 DJANGO SELLING PLANS:")
    print("-"*80)
    for plan in django_plans:
        products_count = plan.products.count()
        print(f"\n{plan.id}. {plan.name}")
        print(f"   Shopify ID: {plan.shopify_id or '❌ NOT PUSHED'}")
        print(f"   Shopify Group ID: {plan.shopify_selling_plan_group_id or '❌ NOT SET'}")
        print(f"   Products in Django: {products_count}")
        print(f"   Billing: {plan.billing_interval_count} {plan.billing_interval}")
        print(f"   Discount: {plan.price_adjustment_value}% off")
        print(f"   Is Active: {'✅ Yes' if plan.is_active else '❌ No'}")
        print(f"   Needs Push: {'⚠️ Yes' if plan.needs_shopify_push else '✅ No'}")
        
        if products_count > 0:
            print(f"   Associated Products:")
            for product in plan.products.all()[:5]:
                print(f"      - {product.title} ({product.shopify_id})")
            if products_count > 5:
                print(f"      ... and {products_count - 5} more")
    
    print("\n" + "="*80)
    print("🔄 CHECKING SHOPIFY STORE")
    print("="*80 + "\n")
    
    # Query Shopify for selling plan groups
    query = """
    query {
      sellingPlanGroups(first: 10) {
        edges {
          node {
            id
            name
            summary
            products(first: 20) {
              edges {
                node {
                  id
                  title
                  status
                }
              }
            }
            sellingPlans(first: 10) {
              edges {
                node {
                  id
                  name
                  category
                  billingPolicy {
                    ... on SellingPlanRecurringBillingPolicy {
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
    
    result = client.execute_graphql_query(query, {})
    
    if "errors" in result:
        print("❌ GraphQL Errors:")
        print(json.dumps(result["errors"], indent=2))
        return
    
    shopify_groups = result.get("data", {}).get("sellingPlanGroups", {}).get("edges", [])
    
    if not shopify_groups:
        print("⚠️ NO SELLING PLAN GROUPS FOUND ON SHOPIFY")
        print("\n💡 This means your selling plans have not been pushed to Shopify yet.")
        print("\n📤 To push selling plans to Shopify:")
        print("   1. Go to Django Admin → Selling Plans")
        print("   2. Select plans to push")
        print("   3. Choose action: 'Push selling plans TO Shopify'")
        print("\n   OR run command:")
        print("   python manage.py test_customer_subscriptions --push-plan <ID>")
        return
    
    print(f"✅ Found {len(shopify_groups)} selling plan groups on Shopify\n")
    
    # Display Shopify plan groups and their products
    print("📋 SHOPIFY SELLING PLAN GROUPS:")
    print("-"*80)
    
    for idx, edge in enumerate(shopify_groups, 1):
        group = edge.get("node", {})
        group_id = group.get("id", "")
        group_name = group.get("name", "Unknown")
        products = group.get("products", {}).get("edges", [])
        product_count = len(products)
        plans = group.get("sellingPlans", {}).get("edges", [])
        
        print(f"\n{idx}. {group_name}")
        print(f"   Group ID: {group_id}")
        print(f"   Product Count: {product_count}")
        print(f"   Plans in Group: {len(plans)}")
        
        # Show plans
        if plans:
            print(f"   Subscription Plans:")
            for plan_edge in plans:
                plan = plan_edge.get("node", {})
                plan_id = plan.get("id", "")
                plan_name = plan.get("name", "Unknown")
                billing = plan.get("billingPolicy", {})
                interval = billing.get("interval", "")
                interval_count = billing.get("intervalCount", 1)
                
                # Get discount
                pricing_policies = plan.get("pricingPolicies", [])
                discount = "N/A"
                if pricing_policies:
                    adj_value = pricing_policies[0].get("adjustmentValue", {})
                    if "percentage" in adj_value:
                        discount = f"{adj_value['percentage']}%"
                
                print(f"      - {plan_name}")
                print(f"        ID: {plan_id}")
                print(f"        Billing: {interval_count} {interval}")
                print(f"        Discount: {discount}")
        
        # Show products
        if products:
            print(f"   Associated Products:")
            for prod_edge in products:
                product = prod_edge.get("node", {})
                prod_id = product.get("id", "")
                prod_title = product.get("title", "Unknown")
                prod_status = product.get("status", "UNKNOWN")
                print(f"      - {prod_title}")
                print(f"        ID: {prod_id}")
                print(f"        Status: {prod_status}")
        else:
            print(f"   ⚠️ NO PRODUCTS ASSOCIATED WITH THIS GROUP")
    
    # Cross-reference: Check which Django plans are on Shopify
    print("\n" + "="*80)
    print("🔗 CROSS-REFERENCE: Django ↔ Shopify")
    print("="*80 + "\n")
    
    shopify_group_ids = [edge.get("node", {}).get("id", "") for edge in shopify_groups]
    
    for plan in django_plans:
        status = "❌ NOT ON SHOPIFY"
        
        if plan.shopify_selling_plan_group_id in shopify_group_ids:
            status = "✅ ON SHOPIFY"
            # Check if it has products
            matching_group = next(
                (edge.get("node", {}) for edge in shopify_groups 
                 if edge.get("node", {}).get("id") == plan.shopify_selling_plan_group_id),
                None
            )
            if matching_group:
                products = matching_group.get("products", {}).get("edges", [])
                product_count = len(products)
                if product_count > 0:
                    status += f" with {product_count} products"
                else:
                    status += " ⚠️ but NO PRODUCTS ATTACHED"
        
        print(f"{plan.name}: {status}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    django_count = django_plans.count()
    shopify_count = len(shopify_groups)
    synced_count = sum(1 for p in django_plans if p.shopify_selling_plan_group_id in shopify_group_ids)
    
    print(f"\n✅ Django Selling Plans: {django_count}")
    print(f"✅ Shopify Plan Groups: {shopify_count}")
    print(f"🔗 Synced Plans: {synced_count}/{django_count}")
    # Check if any Shopify groups have no products
    groups_without_products = 0
    for edge in shopify_groups:
        group = edge.get("node", {})
        products = group.get("products", {}).get("edges", [])
        if len(products) == 0:
            groups_without_products += 1
    
    if groups_without_products > 0:
        print(f"\n⚠️ WARNING: {groups_without_products} plan groups on Shopify have NO products attached")
        print("   Customers won't be able to see subscription options at checkout!")
        print("\n💡 To fix:")
        print("   1. Go to Shopify Admin → Products → Selling Plans")
        print("   2. Click on each plan group")
        print("   3. Click 'Add products'")
        print("   4. Select products and save")
    
    # Check if products in Django are marked correctly
    print("\n📦 PRODUCT ANALYSIS:")
    print("-"*80)
    
    products_with_plans = ShopifyProduct.objects.filter(
        selling_plans__isnull=False
    ).distinct().count()
    
    total_products = ShopifyProduct.objects.count()
    
    print(f"Total Products in Django: {total_products}")
    print(f"Products with Selling Plans: {products_with_plans}")
    print(f"Products without Plans: {total_products - products_with_plans}")
    
    if products_with_plans == 0:
        print("\n⚠️ WARNING: No products in Django are associated with selling plans!")
        print("   Run: python manage.py create_subscription_packages")
        print("   This will associate products with plans and push to Shopify")
    
    print("\n" + "="*80)
    print("✅ CHECK COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    check_selling_plans_on_shopify()
