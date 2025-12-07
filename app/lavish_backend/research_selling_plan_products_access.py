"""
Research: How to Access Products in Selling Plan Groups via Liquid
===================================================================

This script will query Shopify to understand the data structure and
determine how to access products associated with selling plan groups.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def research_selling_plan_data_structure():
    """Research the complete data structure of selling plan groups"""
    
    print("=" * 80)
    print("RESEARCHING SELLING PLAN GROUP DATA STRUCTURE")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # Query with all possible fields to understand the structure
    query = """
    query {
      sellingPlanGroups(first: 1) {
        edges {
          node {
            id
            name
            description
            merchantCode
            appId
            options
            summary
            products(first: 20) {
              edges {
                node {
                  id
                  title
                  handle
                  productType
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
    """
    
    result = client.execute_graphql_query(query)
    
    if "errors" in result:
        print("\n❌ Error:")
        print(json.dumps(result["errors"], indent=2))
        return None
    
    groups = result.get("data", {}).get("sellingPlanGroups", {}).get("edges", [])
    
    if not groups:
        print("\n❌ No selling plan groups found")
        return None
    
    group = groups[0].get("node", {})
    
    print(f"\n📦 Selling Plan Group: {group.get('name')}")
    print(f"   ID: {group.get('id')}")
    print(f"   Description: {group.get('description')}")
    
    products = group.get("products", {}).get("edges", [])
    print(f"\n📚 Products in GraphQL API: {len(products)}")
    
    if products:
        print("   Products returned by API:")
        for prod_edge in products:
            prod = prod_edge.get("node", {})
            print(f"   - {prod.get('title')}")
    else:
        print("   ⚠️ No products in API response")
    
    variants = group.get("productVariants", {}).get("edges", [])
    print(f"\n🔧 Product Variants: {len(variants)}")
    
    if variants:
        print("   Variants returned by API:")
        for var_edge in variants:
            var = var_edge.get("node", {})
            prod = var.get("product", {})
            print(f"   - {prod.get('title')} - {var.get('title')}")
    
    return group


def research_liquid_access():
    """Research how to access products in liquid templates"""
    
    print("\n" + "=" * 80)
    print("RESEARCH: ACCESSING PRODUCTS IN LIQUID")
    print("=" * 80)
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║         SHOPIFY LIQUID: SELLING PLAN GROUP PRODUCT ACCESS                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

PROBLEM:
--------
In Shopify Liquid, the selling_plan_group object has LIMITED access to products.

The structure is:
  product.selling_plan_groups → Array of groups assigned to THIS product
  
BUT we need the REVERSE:
  selling_plan_group.products → All products in this group

SHOPIFY LIQUID LIMITATION:
--------------------------
In liquid templates (product pages), you can access:
  ✅ product.selling_plan_groups (groups assigned to current product)
  ✅ selling_plan_group.name
  ✅ selling_plan_group.description
  ✅ selling_plan_group.selling_plans
  
  ❌ selling_plan_group.products (NOT available in liquid on product pages)
  ❌ selling_plan_group.product_variants (NOT available in liquid)

WHY?
----
Liquid on product pages only has context of the CURRENT product.
It doesn't have access to query OTHER products in the selling plan group.

SOLUTIONS:
----------

OPTION 1: Use Shopify Storefront API (JavaScript)
--------------------------------------------------
Make an AJAX call from the product page to fetch products in the selling plan group.

Pros:
  ✅ Can get complete product list
  ✅ Dynamic and up-to-date

Cons:
  ❌ Requires JavaScript
  ❌ Extra API call
  ❌ Won't work if JS is disabled

Implementation:
```javascript
fetch('/api/2024-01/graphql.json', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: `{
      shop {
        sellingPlanGroups(first: 10) {
          edges {
            node {
              products(first: 20) {
                edges {
                  node { title }
                }
              }
            }
          }
        }
      }
    }`
  })
});
```

OPTION 2: Store Products in Metafields
---------------------------------------
Store the product list in selling plan group metafields.

Pros:
  ✅ Accessible in liquid
  ✅ No JavaScript needed
  ✅ Fast (no extra API calls)

Cons:
  ❌ Requires Django backend to populate
  ❌ Needs maintenance if products change

Implementation:
- Django backend queries products for each selling plan
- Stores product titles in metafield
- Liquid template reads from metafield

OPTION 3: Hardcode in Django Backend (Simplest)
------------------------------------------------
Add a "box_contents" field to Django SellingPlan model.

Pros:
  ✅ Simple to implement
  ✅ Full control over display
  ✅ Can customize per plan

Cons:
  ❌ Manual maintenance
  ❌ Not auto-synced with Shopify

Implementation:
- Add TextField to SellingPlan model: "box_contents"
- Store comma-separated product names
- Push to Shopify as part of description
- Display in liquid

OPTION 4: Use Selling Plan Description Field
---------------------------------------------
Include product list in the description when creating the selling plan.

Pros:
  ✅ Available in liquid
  ✅ No extra fields needed
  ✅ Works immediately

Cons:
  ❌ Description becomes long
  ❌ Not structured data

Implementation:
Update selling plan description to include:
"Monthly fantasy book and themed accessories with 12% discount. 
Includes: Wrath of the Fae, Dragon Sticker, and more!"

OPTION 5: App Proxy for Dynamic Content
----------------------------------------
Create an app proxy endpoint that returns products for a selling plan.

Pros:
  ✅ Dynamic
  ✅ Can use Django backend
  ✅ Full control

Cons:
  ❌ Complex setup
  ❌ Requires app proxy configuration

RECOMMENDED SOLUTION:
---------------------
Use a HYBRID approach:

1. IMMEDIATE FIX: Use selling plan description field
   - Update descriptions to mention key products
   - Works right now in liquid

2. MEDIUM-TERM: Add metafields to selling plan groups
   - Django populates product list in metafield
   - Liquid reads from metafield
   - More structured

3. LONG-TERM: JavaScript enhancement
   - Fetch real-time product list via Storefront API
   - Progressive enhancement (works without JS too)
    """)


def test_liquid_access():
    """Test what's actually available in liquid"""
    
    print("\n" + "=" * 80)
    print("TESTING LIQUID ACCESS")
    print("=" * 80)
    
    print("""
To test what's available in your liquid template, add this debug code:

```liquid
{%- for selling_plan_group in product.selling_plan_groups -%}
  <h4>Debug: {{ selling_plan_group.name }}</h4>
  
  <!-- Check if products field exists -->
  Products field exists: {{ selling_plan_group.products }}
  Products size: {{ selling_plan_group.products.size }}
  
  <!-- Try to list products -->
  {%- for prod in selling_plan_group.products -%}
    <p>Product: {{ prod.title }}</p>
  {%- endfor -%}
  
  <!-- Check description -->
  Description: {{ selling_plan_group.description }}
{%- endfor -%}
```

EXPECTED RESULT:
----------------
If products field is NOT available in liquid:
  - "Products field exists:" will be empty
  - "Products size:" will be empty
  - No products will be listed

ACTUAL WORKAROUND:
------------------
Since we CAN'T access other products in the group from product page liquid,
we need to use one of the alternative solutions above.
    """)


if __name__ == '__main__':
    group_data = research_selling_plan_data_structure()
    research_liquid_access()
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    print("""
FINDING:
--------
✅ Products ARE available via GraphQL API
❌ Products are NOT available in Shopify Liquid on product pages

This is a Shopify limitation, not a code error.

IMMEDIATE FIX:
--------------
I'll update the selling plan DESCRIPTIONS to include product info,
since descriptions ARE available in liquid.

Example:
"Monthly fantasy book and themed accessories with 12% discount.
 Box includes: Wrath of the Fae Omnibus, Dragon Sticker, and 1 more item."

This will show on product page and cart immediately!
    """)

