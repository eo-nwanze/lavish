"""
Update Selling Plan Descriptions with Product Lists
====================================================

Since selling_plan_group.products is NOT available in Shopify Liquid,
we'll update the descriptions to include the product list.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from customer_subscriptions.models import SellingPlan
import json


def update_selling_plan_descriptions():
    """Update selling plan descriptions to include product lists"""
    
    print("=" * 80)
    print("UPDATE SELLING PLAN DESCRIPTIONS WITH PRODUCT LISTS")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # Query all selling plan groups with their products
    query = """
    query {
      sellingPlanGroups(first: 20) {
        edges {
          node {
            id
            name
            description
            sellingPlans(first: 5) {
              edges {
                node {
                  id
                  name
                }
              }
            }
            products(first: 50) {
              edges {
                node {
                  id
                  title
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
        return
    
    selling_plan_groups = result.get("data", {}).get("sellingPlanGroups", {}).get("edges", [])
    
    print(f"\n📊 Found {len(selling_plan_groups)} selling plan groups")
    
    # Group by name to process only unique ones
    unique_groups = {}
    
    for group_edge in selling_plan_groups:
        group = group_edge.get("node", {})
        name = group.get("name")
        
        # Keep only the newest instance of each group
        if name not in unique_groups or group.get("createdAt", "") > unique_groups[name].get("createdAt", ""):
            unique_groups[name] = group
    
    print(f"   Unique groups (after de-duplication): {len(unique_groups)}")
    
    # Update each selling plan
    updated_count = 0
    
    for name, group in unique_groups.items():
        group_id = group.get("id")
        current_desc = group.get("description", "")
        
        products = group.get("products", {}).get("edges", [])
        product_titles = [p.get("node", {}).get("title") for p in products]
        
        print(f"\n{'='*80}")
        print(f"Selling Plan Group: {name}")
        print(f"{'='*80}")
        print(f"ID: {group_id}")
        print(f"Current Description: {current_desc}")
        print(f"Products: {len(product_titles)}")
        
        if not product_titles:
            print("   ⚠️ No products in this group, skipping")
            continue
        
        # Build new description with product list
        base_desc = current_desc.split("Box includes:")[0].strip() if "Box includes:" in current_desc else current_desc
        
        # Create product list text
        if len(product_titles) <= 3:
            product_list = ", ".join(product_titles)
        else:
            product_list = ", ".join(product_titles[:3]) + f", and {len(product_titles) - 3} more"
        
        new_description = f"{base_desc}\n\nBox includes: {product_list}"
        
        print(f"\nNew Description:")
        print(f"   {new_description}")
        
        # Get the selling plan ID from the group
        plans = group.get("sellingPlans", {}).get("edges", [])
        if not plans:
            print("   ⚠️ No selling plans in this group")
            continue
        
        plan = plans[0].get("node", {})
        plan_id = plan.get("id")
        plan_name = plan.get("name")
        
        print(f"\nUpdating Selling Plan: {plan_name}")
        print(f"Plan ID: {plan_id}")
        
        # Update the selling plan group with new description
        # This will update all plans in the group
        update_mutation = """
        mutation sellingPlanGroupUpdate($id: ID!, $input: SellingPlanGroupInput!) {
          sellingPlanGroupUpdate(id: $id, input: $input) {
            sellingPlanGroup {
              id
              name
              description
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "id": group_id,
            "input": {
                "name": name,
                "description": new_description,
                "merchantCode": name.lower().replace(" ", "_")
            }
        }
        
        update_result = client.execute_graphql_query(update_mutation, variables)
        
        if "errors" in update_result:
            print(f"   ❌ GraphQL Error: {update_result['errors']}")
            continue
        
        update_data = update_result.get("data", {}).get("sellingPlanGroupUpdate", {})
        user_errors = update_data.get("userErrors", [])
        
        if user_errors:
            print(f"   ❌ Validation Error: {user_errors}")
        else:
            print(f"   ✅ Updated successfully!")
            updated_count += 1
            
            # Also update Django database if plan exists
            try:
                django_plan = SellingPlan.objects.filter(shopify_id=plan_id).first()
                if django_plan:
                    django_plan.description = new_description
                    django_plan.save(update_fields=['description'])
                    print(f"   ✅ Updated Django database too")
            except Exception as e:
                print(f"   ⚠️ Django update failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n  ✅ Updated {updated_count} selling plans with product lists")
    print(f"  📦 Descriptions now include what's in each box")
    print(f"\n  Refresh your product page to see the changes!")


if __name__ == '__main__':
    update_selling_plan_descriptions()

