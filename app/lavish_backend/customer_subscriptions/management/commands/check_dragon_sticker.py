"""
Comprehensive check - Query Shopify for Save a Horse Dragon Sticker selling plans
"""

from django.core.management.base import BaseCommand
from products.models import ShopifyProduct
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient


class Command(BaseCommand):
    help = 'Check Dragon sticker selling plans in Shopify'
    
    def handle(self, *args, **options):
        try:
            prod = ShopifyProduct.objects.get(handle='save-a-horse-ride-a-dragon-sticker')
        except ShopifyProduct.DoesNotExist:
            self.stdout.write(self.style.ERROR("Product not found in Django!"))
            return
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS(f"Checking: {prod.title}"))
        self.stdout.write(f"Handle: {prod.handle}")
        self.stdout.write(f"Django ID: {prod.id}")
        self.stdout.write(f"Shopify ID: {prod.shopify_id}")
        self.stdout.write("="*80)
        
        # Check Django selling plans
        django_plans = prod.selling_plans.all()
        self.stdout.write(f"\nDjango - Selling plans associated: {django_plans.count()}")
        for plan in django_plans:
            self.stdout.write(f"  - {plan.name}: {plan.price_adjustment_value}%")
        
        # Query Shopify
        client = EnhancedShopifyAPIClient()
        
        query = """
        query getProduct($id: ID!) {
          product(id: $id) {
            id
            title
            sellingPlanGroups(first: 10) {
              edges {
                node {
                  id
                  name
                  sellingPlans(first: 10) {
                    edges {
                      node {
                        id
                        name
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
        }
        """
        
        variables = {"id": prod.shopify_id}
        result = client.execute_graphql_query(query, variables)
        
        if result:
            product = result.get("data", {}).get("product", {})
            groups = product.get("sellingPlanGroups", {}).get("edges", [])
            
            self.stdout.write(f"\nShopify - Selling plan groups: {len(groups)}\n")
            
            if groups:
                for idx, group_edge in enumerate(groups, 1):
                    group = group_edge.get("node", {})
                    self.stdout.write(f"\n{idx}. {group.get('name')}")
                    self.stdout.write(f"   Group ID: {group.get('id')}")
                    
                    plans = group.get("sellingPlans", {}).get("edges", [])
                    for plan_edge in plans:
                        plan = plan_edge.get("node", {})
                        self.stdout.write(f"\n   Plan: {plan.get('name')}")
                        self.stdout.write(f"   Plan ID: {plan.get('id')}")
                        
                        policies = plan.get("pricingPolicies", [])
                        if policies:
                            adj_value = policies[0].get("adjustmentValue", {})
                            percentage = adj_value.get("percentage", 0)
                            if percentage > 0:
                                self.stdout.write(self.style.SUCCESS(f"   Shopify has: {percentage}% ✓"))
                            else:
                                self.stdout.write(self.style.ERROR(f"   Shopify has: {percentage}% ✗ WRONG!"))
                        else:
                            self.stdout.write(self.style.ERROR("   NO PRICING POLICY!"))
            else:
                self.stdout.write(self.style.ERROR("NO selling plan groups in Shopify!"))
        else:
            self.stdout.write(self.style.ERROR("No response from Shopify"))
        
        self.stdout.write("\n" + "="*80 + "\n")

