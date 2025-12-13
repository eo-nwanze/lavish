"""
Remove OLD selling plan groups from products and keep only the UPDATED ones
"""

from django.core.management.base import BaseCommand
from products.models import ShopifyProduct
from customer_subscriptions.models import SellingPlan
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient


class Command(BaseCommand):
    help = 'Remove old duplicate selling plan groups from products in Shopify'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("REMOVE OLD SELLING PLAN GROUPS FROM PRODUCTS"))
        self.stdout.write("="*80 + "\n")
        
        # Get all Django selling plans with their current group IDs
        plans = SellingPlan.objects.filter(shopify_selling_plan_group_id__isnull=False)
        
        # Map of correct group IDs
        correct_groups = {plan.shopify_selling_plan_group_id for plan in plans}
        self.stdout.write(f"Current CORRECT selling plan groups: {len(correct_groups)}")
        for plan in plans:
            self.stdout.write(f"  - {plan.name}: {plan.shopify_selling_plan_group_id}")
        
        # Check all products
        self.stdout.write(f"\nChecking products...\n")
        
        client = EnhancedShopifyAPIClient()
        products = ShopifyProduct.objects.filter(selling_plans__isnull=False).distinct()
        
        for product in products:
            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write(f"Product: {product.title}")
            self.stdout.write(f"ID: {product.shopify_id}")
            
            # Query what groups are currently attached
            query = """
            query getProduct($id: ID!) {
              product(id: $id) {
                id
                sellingPlanGroups(first: 20) {
                  edges {
                    node {
                      id
                      name
                    }
                  }
                }
              }
            }
            """
            
            result = client.execute_graphql_query(query, {"id": product.shopify_id})
            if not result:
                self.stdout.write(self.style.ERROR("  No response from Shopify"))
                continue
            
            shopify_product = result.get("data", {}).get("product", {})
            groups = shopify_product.get("sellingPlanGroups", {}).get("edges", [])
            
            self.stdout.write(f"  Currently has {len(groups)} groups attached")
            
            # Find groups to remove (not in our correct list)
            groups_to_remove = []
            groups_to_keep = []
            
            for group_edge in groups:
                group = group_edge.get("node", {})
                group_id = group.get("id")
                group_name = group.get("name")
                
                if group_id in correct_groups:
                    groups_to_keep.append(f"{group_name} ({group_id})")
                else:
                    groups_to_remove.append(group_id)
                    self.stdout.write(self.style.WARNING(f"    - Will remove: {group_name} ({group_id})"))
            
            if groups_to_remove:
                # Remove old groups
                mutation = """
                mutation sellingPlanGroupRemoveProducts($id: ID!, $productIds: [ID!]!) {
                  sellingPlanGroupRemoveProducts(id: $id, productIds: $productIds) {
                    removedProductIds
                    userErrors {
                      field
                      message
                    }
                  }
                }
                """
                
                for old_group_id in groups_to_remove:
                    variables = {
                        "id": old_group_id,
                        "productIds": [product.shopify_id]
                    }
                    
                    remove_result = client.execute_graphql_query(mutation, variables)
                    if remove_result:
                        data = remove_result.get("data", {}).get("sellingPlanGroupRemoveProducts", {})
                        errors = data.get("userErrors", [])
                        if errors:
                            self.stdout.write(self.style.ERROR(f"    Failed: {errors[0].get('message')}"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"    Removed: {old_group_id}"))
                
                self.stdout.write(self.style.SUCCESS(f"  Cleanup complete! Keeping {len(groups_to_keep)} correct groups"))
            else:
                self.stdout.write(self.style.SUCCESS("  No old groups to remove"))
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("CLEANUP COMPLETE!"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Hard refresh browser (Ctrl+Shift+R)")
        self.stdout.write("2. Check if discounts now show correctly")
        self.stdout.write("="*80 + "\n")

