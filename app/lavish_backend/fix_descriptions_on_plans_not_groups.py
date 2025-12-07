"""
Fix: Put Descriptions on SELLING PLANS Instead of GROUPS
==========================================================

Since liquid can't access group.description, put it on plan.description
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def update_plan_descriptions():
    """Update individual selling plan descriptions with product lists"""
    
    print("=" * 80)
    print("UPDATING SELLING PLAN DESCRIPTIONS (NOT GROUPS)")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # Query all selling plan groups with their products and plans
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
        print("\n❌ Error:")
        print(json.dumps(result["errors"], indent=2))
        return
    
    groups = result.get("data", {}).get("sellingPlanGroups", {}).get("edges", [])
    
    # De-duplicate groups
    unique_groups = {}
    for group_edge in groups:
        group = group_edge.get("node", {})
        name = group.get("name")
        if name not in unique_groups:
            unique_groups[name] = group
    
    print(f"\n📦 Found {len(unique_groups)} unique selling plan groups")
    
    updated_count = 0
    
    for name, group in unique_groups.items():
        group_desc = group.get("description", "")
        products = group.get("products", {}).get("edges", [])
        product_titles = [p.get("node", {}).get("title") for p in products]
        
        # Extract base description (before "Box includes:")
        if "Box includes:" in group_desc:
            base_desc = group_desc.split("Box includes:")[0].strip()
            # Get the product list part
            product_list_part = group_desc.split("Box includes:")[1].strip()
        else:
            base_desc = group_desc
            # Build product list from API
            if len(product_titles) <= 3:
                product_list_part = ", ".join(product_titles)
            else:
                product_list_part = ", ".join(product_titles[:3]) + f", and {len(product_titles) - 3} more"
        
        full_description = f"{base_desc}\n\nBox includes: {product_list_part}" if base_desc else f"Box includes: {product_list_part}"
        
        print(f"\n{'='*80}")
        print(f"Group: {name}")
        print(f"{'='*80}")
        print(f"Description to add:")
        print(f"  {full_description[:150]}...")
        
        # Get all plans in this group
        plans = group.get("sellingPlans", {}).get("edges", [])
        
        if not plans:
            print("  ⚠️ No plans in this group")
            continue
        
        # Build update data for all plans in this group
        all_plans_data = []
        for p_edge in plans:
            p = p_edge.get("node", {})
            plan_id = p.get("id")
            plan_name = p.get("name")
            
            print(f"\nPreparing update for plan: {plan_name}")
            
            all_plans_data.append({
                "id": plan_id,
                "name": plan_name,
                "description": full_description,  # Add description to each plan
                "options": ["Subscription"],
                "position": 1
            })
        
        # Update the entire group with all plans having descriptions
        mutation = """
        mutation updateGroup($id: ID!, $input: SellingPlanGroupInput!) {
          sellingPlanGroupUpdate(id: $id, input: $input) {
            sellingPlanGroup {
              id
              name
              sellingPlans(first: 10) {
                edges {
                  node {
                    id
                    name
                    description
                  }
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "id": group.get("id"),
            "input": {
                "name": name,
                "description": group_desc,  # Keep group description
                "merchantCode": name.lower().replace(" ", "_"),
                "sellingPlansToUpdate": all_plans_data
            }
        }
        
        print(f"\n🔄 Updating group with {len(all_plans_data)} plan(s)...")
        
        update_result = client.execute_graphql_query(mutation, variables)
        
        if "errors" in update_result:
            print(f"❌ GraphQL Error: {update_result['errors']}")
            continue
        
        update_data = update_result.get("data", {}).get("sellingPlanGroupUpdate", {})
        user_errors = update_data.get("userErrors", [])
        
        if user_errors:
            print(f"❌ User Error: {user_errors}")
        else:
            print(f"✅ Updated successfully!")
            # Verify descriptions were added
            updated_plans = update_data.get("sellingPlanGroup", {}).get("sellingPlans", {}).get("edges", [])
            for up_edge in updated_plans:
                up = up_edge.get("node", {})
                desc_len = len(up.get("description") or "")
                print(f"  - {up.get('name')}: {desc_len} chars")
            updated_count += len(all_plans_data)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Updated {updated_count} selling plans with descriptions")
    print(f"📝 Descriptions now on PLAN level (accessible in liquid!)")


if __name__ == '__main__':
    update_plan_descriptions()
    
    print("\n" + "=" * 80)
    print("NEXT STEP")
    print("=" * 80)
    print("""
The descriptions are now on selling_plan.description instead of
selling_plan_group.description.

Your liquid template already checks both:
  1. selling_plan_group.description (was empty)
  2. selling_plan.description (now has the content!)

Refresh your browser and the product list should appear!
    """)

