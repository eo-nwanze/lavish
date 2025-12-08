"""
Investigate Duplicate Selling Plans
====================================

Check if selling plans are duplicated and which products are associated.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json
from collections import defaultdict


def investigate_selling_plans():
    """Investigate duplicate selling plans and their product associations"""
    
    print("=" * 80)
    print("INVESTIGATING DUPLICATE SELLING PLANS")
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
            merchantCode
            createdAt
            sellingPlans(first: 10) {
              edges {
                node {
                  id
                  name
                  description
                  options
                }
              }
            }
            products(first: 50) {
              edges {
                node {
                  id
                  title
                  handle
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
    
    print(f"\n📊 Found {len(selling_plan_groups)} selling plan groups\n")
    
    # Group by name to find duplicates
    groups_by_name = defaultdict(list)
    
    for group_edge in selling_plan_groups:
        group = group_edge.get("node", {})
        name = group.get("name")
        groups_by_name[name].append(group)
    
    # Find Wrath book specifically
    wrath_products = []
    
    print("\n" + "=" * 80)
    print("ANALYZING DUPLICATE SELLING PLAN GROUPS")
    print("=" * 80)
    
    for name, groups in groups_by_name.items():
        if len(groups) > 1:
            print(f"\n⚠️ DUPLICATE: '{name}' appears {len(groups)} times")
            print("-" * 80)
            
            for idx, group in enumerate(groups, 1):
                print(f"\n  Instance #{idx}:")
                print(f"  ID: {group.get('id')}")
                print(f"  Created: {group.get('createdAt')}")
                print(f"  Description: {group.get('description', 'N/A')}")
                
                products = group.get("products", {}).get("edges", [])
                print(f"  Products: {len(products)}")
                
                for prod_edge in products:
                    prod = prod_edge.get("node", {})
                    title = prod.get("title")
                    print(f"    - {title}")
                    
                    # Check if it's a Wrath book
                    if "wrath" in title.lower():
                        wrath_products.append({
                            "product": title,
                            "group_name": name,
                            "group_id": group.get("id"),
                            "created": group.get("createdAt")
                        })
                
                plans = group.get("sellingPlans", {}).get("edges", [])
                print(f"  Selling Plans: {len(plans)}")
                for plan_edge in plans:
                    plan = plan_edge.get("node", {})
                    print(f"    Plan ID: {plan.get('id')}")
                    print(f"    Plan Name: {plan.get('name')}")
                    print(f"    Options: {plan.get('options')}")
    
    # Show Wrath book associations
    print("\n" + "=" * 80)
    print("WRATH BOOK SELLING PLAN ASSOCIATIONS")
    print("=" * 80)
    
    if wrath_products:
        print(f"\n📚 Found {len(wrath_products)} associations for Wrath books:")
        for assoc in wrath_products:
            print(f"\n  Product: {assoc['product']}")
            print(f"  Selling Plan Group: {assoc['group_name']}")
            print(f"  Group ID: {assoc['group_id']}")
            print(f"  Created: {assoc['created']}")
    else:
        print("\n❌ No Wrath books found in selling plan groups")
    
    # Provide recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    duplicates = {name: len(groups) for name, groups in groups_by_name.items() if len(groups) > 1}
    
    if duplicates:
        print("\n⚠️ You have duplicate selling plan groups:")
        for name, count in duplicates.items():
            print(f"  - '{name}': {count} instances")
        
        print("\n💡 SOLUTIONS:")
        print("\n1. DELETE DUPLICATES IN SHOPIFY ADMIN:")
        print("   - Go to Shopify Admin → Products → Subscriptions")
        print("   - Keep only the NEWEST version of each plan")
        print("   - Delete older duplicates")
        
        print("\n2. FILTER DUPLICATES IN CODE (Quick Fix):")
        print("   - Update liquid template to show only unique selling plans")
        print("   - Group by name and show only one instance")
        
        print("\n3. KEEP ALL IF INTENTIONAL:")
        print("   - If different groups target different products, keep all")
        print("   - But give them UNIQUE names (e.g., 'Fantasy Lover's Monthly - Books')")
    
    # Check for the "SellingPlanOptionDrop" issue
    print("\n" + "=" * 80)
    print("INVESTIGATING 'SellingPlanOptionDrop' DISPLAY ISSUE")
    print("=" * 80)
    
    print("\n🔍 Checking what selling_plan.options contains:")
    
    for group_edge in selling_plan_groups:
        group = group_edge.get("node", {})
        plans = group.get("sellingPlans", {}).get("edges", [])
        
        for plan_edge in plans:
            plan = plan_edge.get("node", {})
            options = plan.get("options", [])
            
            if options and "SellingPlanOptionDrop" in str(options):
                print(f"\n  Plan: {plan.get('name')}")
                print(f"  Options: {options}")
                print("  ⚠️ This is NOT user-friendly text!")
    
    print("\n💡 FIX: The 'options' field contains delivery frequency info,")
    print("   not a human-readable description. We should display:")
    print("   - Billing interval (e.g., 'Every 1 month')")
    print("   - Delivery interval")
    print("   - Or use the selling plan description instead")
    
    return groups_by_name


def generate_cleanup_mutations(groups_by_name):
    """Generate GraphQL mutations to delete duplicate selling plan groups"""
    
    print("\n" + "=" * 80)
    print("CLEANUP MUTATIONS (OPTIONAL)")
    print("=" * 80)
    
    duplicates_to_delete = []
    
    for name, groups in groups_by_name.items():
        if len(groups) > 1:
            # Sort by creation date, keep newest
            sorted_groups = sorted(groups, key=lambda x: x.get("createdAt", ""), reverse=True)
            
            # Groups to delete (all except newest)
            to_delete = sorted_groups[1:]
            
            print(f"\n📦 '{name}':")
            print(f"  Keep: {sorted_groups[0].get('id')} (created {sorted_groups[0].get('createdAt')})")
            print(f"  Delete: {len(to_delete)} older instance(s)")
            
            for group in to_delete:
                duplicates_to_delete.append({
                    "id": group.get("id"),
                    "name": name,
                    "created": group.get("createdAt")
                })
    
    if duplicates_to_delete:
        print("\n" + "=" * 80)
        print("GRAPHQL MUTATIONS TO DELETE DUPLICATES")
        print("=" * 80)
        
        print("\n⚠️ WARNING: This will PERMANENTLY delete the older selling plan groups!")
        print("Make sure to backup any important data first.\n")
        
        for dup in duplicates_to_delete:
            print(f"# Delete: {dup['name']} (created {dup['created']})")
            print("mutation {")
            print(f"  sellingPlanGroupDelete(id: \"{dup['id']}\") {{")
            print("    deletedSellingPlanGroupId")
            print("    userErrors {")
            print("      field")
            print("      message")
            print("    }")
            print("  }")
            print("}\n")
    
    return duplicates_to_delete


if __name__ == '__main__':
    groups_by_name = investigate_selling_plans()
    
    if groups_by_name:
        duplicates = generate_cleanup_mutations(groups_by_name)
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        total_duplicates = sum(1 for groups in groups_by_name.values() if len(groups) > 1)
        
        print(f"\n  Duplicate selling plan groups: {total_duplicates}")
        print(f"  Instances to potentially delete: {len(duplicates)}")
        
        print("\n✅ NEXT STEPS:")
        print("  1. Review the duplicate selling plan groups above")
        print("  2. Decide: Delete duplicates OR keep all with unique names")
        print("  3. Fix the liquid template to show proper descriptions")
        print("     (instead of 'SellingPlanOptionDrop')")




