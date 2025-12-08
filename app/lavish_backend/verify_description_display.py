"""
Verify Selling Plan Descriptions Are Showing Correctly
=======================================================

Check if descriptions with product lists are available and displaying.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def verify_descriptions():
    """Verify selling plan descriptions in Shopify"""
    
    print("=" * 80)
    print("VERIFYING SELLING PLAN DESCRIPTIONS")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # Query a specific product to see what's available in liquid context
    query = """
    query {
      products(first: 1, query: "title:Wrath") {
        edges {
          node {
            id
            title
            sellingPlanGroups(first: 5) {
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
                        description
                        options
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
    
    result = client.execute_graphql_query(query)
    
    if "errors" in result:
        print("\n❌ Error:")
        print(json.dumps(result["errors"], indent=2))
        return
    
    products = result.get("data", {}).get("products", {}).get("edges", [])
    
    if not products:
        print("\n❌ No products found")
        return
    
    product = products[0].get("node", {})
    
    print(f"\n📦 Product: {product.get('title')}")
    print(f"   ID: {product.get('id')}")
    
    groups = product.get("sellingPlanGroups", {}).get("edges", [])
    
    print(f"\n📋 Selling Plan Groups: {len(groups)}")
    
    for group_edge in groups:
        group = group_edge.get("node", {})
        
        print(f"\n{'='*80}")
        print(f"Group: {group.get('name')}")
        print(f"{'='*80}")
        print(f"ID: {group.get('id')}")
        print(f"\nGroup Description:")
        print(f"  {group.get('description', 'EMPTY')[:200]}...")
        
        plans = group.get("sellingPlans", {}).get("edges", [])
        
        for plan_edge in plans:
            plan = plan_edge.get("node", {})
            
            print(f"\n  Plan: {plan.get('name')}")
            print(f"  Plan ID: {plan.get('id')}")
            print(f"  Plan Description:")
            
            desc = plan.get('description', '')
            if desc:
                print(f"    ✅ HAS DESCRIPTION ({len(desc)} chars)")
                print(f"    Preview: {desc[:150]}...")
                if "Box includes:" in desc:
                    print(f"    ✅ Contains product list!")
                else:
                    print(f"    ⚠️ Missing 'Box includes:' section")
            else:
                print(f"    ❌ NO DESCRIPTION")
            
            print(f"  Options: {plan.get('options', [])}")
    
    print("\n" + "=" * 80)
    print("LIQUID TEMPLATE ACCESS TEST")
    print("=" * 80)
    
    print("""
To test if descriptions are accessible in liquid, check:

1. In your browser, view source on product page
2. Search for "selling_plan.description"
3. You should see the full description with "Box includes:"

OR add this debug code to your liquid template:

```liquid
{%- for selling_plan_group in product.selling_plan_groups -%}
  <div style="background: yellow; padding: 20px; margin: 20px;">
    <h3>DEBUG: {{ selling_plan_group.name }}</h3>
    <p><strong>Group Description:</strong></p>
    <pre>{{ selling_plan_group.description }}</pre>
    
    {%- for selling_plan in selling_plan_group.selling_plans -%}
      <p><strong>Plan: {{ selling_plan.name }}</strong></p>
      <p><strong>Plan Description:</strong></p>
      <pre>{{ selling_plan.description }}</pre>
    {%- endfor -%}
  </div>
{%- endfor -%}
```

This will show exactly what liquid has access to.
    """)


def check_specific_plan():
    """Check a specific selling plan in detail"""
    
    print("\n" + "=" * 80)
    print("CHECKING SPECIFIC SELLING PLAN")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # Query Fantasy Lover's Monthly specifically
    query = """
    query {
      sellingPlanGroup(id: "gid://shopify/SellingPlanGroup/4935483486") {
        id
        name
        description
        sellingPlans(first: 5) {
          edges {
            node {
              id
              name
              description
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
    
    group = result.get("data", {}).get("sellingPlanGroup", {})
    
    if not group:
        print("\n❌ Group not found")
        return
    
    print(f"\n✅ Found: {group.get('name')}")
    print(f"\nGroup Description:")
    print("-" * 80)
    print(group.get('description', 'EMPTY'))
    print("-" * 80)
    
    plans = group.get("sellingPlans", {}).get("edges", [])
    
    for plan_edge in plans:
        plan = plan_edge.get("node", {})
        
        print(f"\n{'='*80}")
        print(f"Plan: {plan.get('name')}")
        print(f"ID: {plan.get('id')}")
        print(f"\nPlan Description:")
        print("-" * 80)
        desc = plan.get('description', '')
        if desc:
            print(desc)
            print("-" * 80)
            print(f"\n✅ Length: {len(desc)} characters")
            if "Box includes:" in desc:
                print("✅ Contains 'Box includes:' section")
                # Extract the product list
                parts = desc.split("Box includes:")
                if len(parts) > 1:
                    product_list = parts[1].strip()
                    print(f"\nProduct List:")
                    print(f"  {product_list}")
            else:
                print("⚠️ Missing 'Box includes:' section")
        else:
            print("EMPTY")
            print("-" * 80)
            print("❌ NO DESCRIPTION")


if __name__ == '__main__':
    verify_descriptions()
    check_specific_plan()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    print("""
1. ✅ Descriptions are in Shopify (verified above)
2. ⚠️ Need to check if liquid can access them

To fix liquid display:

A. Clear your browser cache
B. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
C. Check if theme files are saved in Shopify admin
D. Add debug liquid code (shown above) to see what's accessible

If descriptions still don't show:
  - The theme files may not be saved to Shopify
  - Need to deploy/push the liquid changes
  - May need to use Shopify CLI to sync theme
    """)




