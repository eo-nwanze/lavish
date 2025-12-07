"""
Debug: Why Subscription Descriptions Aren't Showing in Liquid
==============================================================

Check all possible reasons the description might not be rendering.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def check_description_accessibility():
    """Check if descriptions are accessible and formatted correctly"""
    
    print("=" * 80)
    print("DEBUGGING LIQUID DESCRIPTION DISPLAY")
    print("=" * 80)
    
    client = EnhancedShopifyAPIClient()
    
    # Query exactly as liquid would access it
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
        print("\n❌ API Error:")
        print(json.dumps(result["errors"], indent=2))
        return
    
    group = result.get("data", {}).get("sellingPlanGroup", {})
    
    print(f"\n✅ Group: {group.get('name')}")
    print(f"   ID: {group.get('id')}")
    
    group_desc = group.get('description', '')
    
    print(f"\n{'='*80}")
    print("GROUP DESCRIPTION")
    print(f"{'='*80}")
    print(f"Length: {len(group_desc)} characters")
    print(f"Is blank: {not group_desc}")
    print(f"\nFull text:")
    print("-" * 80)
    print(group_desc if group_desc else "(EMPTY)")
    print("-" * 80)
    
    # Check for special characters that might break liquid
    if group_desc:
        print(f"\nSpecial characters check:")
        print(f"  - Contains newlines: {chr(10) in group_desc}")
        has_quotes = ('"' in group_desc) or ("'" in group_desc)
        print(f"  - Contains quotes: {has_quotes}")
        has_html = ('<' in group_desc) or ('>' in group_desc)
        print(f"  - Contains HTML: {has_html}")
        print(f"  - Line break type: \\n (Unix)")
    
    plans = group.get("sellingPlans", {}).get("edges", [])
    
    for plan_edge in plans:
        plan = plan_edge.get("node", {})
        plan_desc = plan.get('description') or ''
        
        print(f"\n{'='*80}")
        print(f"PLAN: {plan.get('name')}")
        print(f"{'='*80}")
        print(f"Length: {len(plan_desc)} characters")
        print(f"Is blank: {not plan_desc}")
        if plan_desc:
            print(f"Text: {plan_desc[:100]}...")
    
    print("\n" + "=" * 80)
    print("LIQUID TEMPLATE CHECK")
    print("=" * 80)
    
    print("""
The liquid template should have this code:

```liquid
{%- assign group_desc = selling_plan_group.description -%}

{%- if group_desc != blank -%}
  <div style="...">{{ group_desc }}</div>
{%- endif -%}
```

If the description still doesn't show, it means:

1. ❌ Theme files not deployed to Shopify
   - Check Shopify CLI is running
   - Check theme.liquid includes the snippet
   - Check theme is published

2. ❌ Liquid cache issue
   - Clear Shopify's liquid cache
   - Hard refresh browser (Ctrl+Shift+R)

3. ❌ Description contains invalid liquid syntax
   - Check for {{ or {% in description
   - These would break liquid rendering

4. ❌ CSP (Content Security Policy) blocking
   - Check browser console for CSP errors

Let me check the description for liquid syntax...
    """)
    
    if group_desc:
        print("\nChecking description for liquid syntax:")
        has_liquid = ('{{' in group_desc) or ('{%' in group_desc)
        if has_liquid:
            print("  ⚠️ WARNING: Description contains liquid tags!")
            print("  This will break rendering!")
        else:
            print("  ✅ No liquid tags found - description is safe")


def suggest_fix():
    """Suggest how to fix the issue"""
    
    print("\n" + "=" * 80)
    print("RECOMMENDED FIXES")
    print("=" * 80)
    
    print("""
1. VERIFY THEME DEPLOYMENT
   ========================
   
   Your liquid changes need to be in Shopify's theme files.
   
   Check if you're using Shopify CLI theme development:
   
   cd app/lavish_frontend
   shopify theme dev --store=7fa66c-ac.myshopify.com
   
   Or if you need to push the theme:
   
   shopify theme push --store=7fa66c-ac.myshopify.com
   
   
2. ADD DEBUG OUTPUT
   =================
   
   Add this to your liquid template TEMPORARILY:
   
   ```liquid
   <div style="background: yellow; padding: 20px; margin: 20px 0;">
     <h3>DEBUG INFO</h3>
     <p>Group name: {{ selling_plan_group.name }}</p>
     <p>Group desc size: {{ selling_plan_group.description | size }}</p>
     <p>Group desc blank?: {% if selling_plan_group.description == blank %}YES{% else %}NO{% endif %}</p>
     <hr>
     <pre style="white-space: pre-wrap; font-size: 11px;">{{ selling_plan_group.description }}</pre>
   </div>
   ```
   
   This will show you EXACTLY what liquid sees!
   
   
3. CHECK IF FILES ARE SAVED
   =========================
   
   - Open Shopify Admin
   - Go to Online Store > Themes > Customize
   - Click "..." > Edit code
   - Find snippets/subscription-purchase-options.liquid
   - Verify it has the latest code
   
   
4. CLEAR ALL CACHES
   ==================
   
   - Clear browser cache
   - Hard refresh (Ctrl+Shift+R)
   - Try incognito/private window
   - Clear Shopify cache (re-publish theme)
    """)


if __name__ == '__main__':
    check_description_accessibility()
    suggest_fix()
    
    print("\n" + "=" * 80)
    print("NEXT STEP")
    print("=" * 80)
    print("""
Add the debug liquid code to your template to see what's actually accessible!

Then report back what you see in the yellow debug box.
    """)

