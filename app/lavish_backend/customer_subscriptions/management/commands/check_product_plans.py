"""
Check what Shopify actually has stored for selling plan discounts on the sticker product
"""

from django.core.management.base import BaseCommand
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient


class Command(BaseCommand):
    help = 'Check selling plans on Save a Horse Sticker product in Shopify'
    
    def handle(self, *args, **options):
        client = EnhancedShopifyAPIClient()
        
        query = """
        {
          products(first: 1, query: "title:*Save a Horse*Sticker*") {
            edges {
              node {
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
          }
        }
        """
        
        result = client.execute_graphql_query(query, {})
        
        if result:
            products = result.get("data", {}).get("products", {}).get("edges", [])
            
            if products:
                product = products[0].get("node", {})
                self.stdout.write(f"\n{'='*80}")
                self.stdout.write(self.style.SUCCESS(f"Product: {product.get('title')}"))
                self.stdout.write(f"Shopify ID: {product.get('id')}")
                self.stdout.write("="*80 + "\n")
                
                groups = product.get("sellingPlanGroups", {}).get("edges", [])
                
                if groups:
                    self.stdout.write(f"Found {len(groups)} selling plan group(s) attached:\n")
                    
                    for idx, group_edge in enumerate(groups, 1):
                        group = group_edge.get("node", {})
                        self.stdout.write(f"\n{idx}. Group: {group.get('name')}")
                        self.stdout.write(f"   ID: {group.get('id')}")
                        
                        plans = group.get("sellingPlans", {}).get("edges", [])
                        for plan_edge in plans:
                            plan = plan_edge.get("node", {})
                            self.stdout.write(f"\n   Plan: {plan.get('name')}")
                            self.stdout.write(f"   ID: {plan.get('id')}")
                            
                            policies = plan.get("pricingPolicies", [])
                            if policies:
                                adj_value = policies[0].get("adjustmentValue", {})
                                percentage = adj_value.get("percentage", 0)
                                if percentage > 0:
                                    self.stdout.write(self.style.SUCCESS(f"   Discount: {percentage}%"))
                                else:
                                    self.stdout.write(self.style.ERROR(f"   Discount: {percentage}% (WRONG!)"))
                            else:
                                self.stdout.write(self.style.ERROR("   Discount: NONE"))
                else:
                    self.stdout.write(self.style.WARNING("NO selling plan groups attached to this product!"))
            else:
                self.stdout.write(self.style.ERROR("Product not found!"))
        else:
            self.stdout.write(self.style.ERROR("No response from Shopify"))

