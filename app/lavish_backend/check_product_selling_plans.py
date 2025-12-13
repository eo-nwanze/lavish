"""
Query Shopify directly to see what selling plans a product actually has
"""

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json

client = EnhancedShopifyAPIClient()

# Query for the "Save a Horse" product
query = """
{
  products(first: 1, query: "title:*Save a Horse*") {
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
        print(f"\n{'='*80}")
        print(f"Product: {product.get('title')}")
        print(f"Shopify ID: {product.get('id')}")
        print(f"{'='*80}\n")
        
        groups = product.get("sellingPlanGroups", {}).get("edges", [])
        
        if groups:
            print(f"Found {len(groups)} selling plan group(s) attached:\n")
            
            for idx, group_edge in enumerate(groups, 1):
                group = group_edge.get("node", {})
                print(f"{idx}. Group: {group.get('name')}")
                print(f"   ID: {group.get('id')}")
                
                plans = group.get("sellingPlans", {}).get("edges", [])
                for plan_edge in plans:
                    plan = plan_edge.get("node", {})
                    print(f"   - Plan: {plan.get('name')}")
                    print(f"     ID: {plan.get('id')}")
                    
                    policies = plan.get("pricingPolicies", [])
                    if policies:
                        adj_value = policies[0].get("adjustmentValue", {})
                        percentage = adj_value.get("percentage", 0)
                        print(f"     Discount: {percentage}%")
                    else:
                        print(f"     Discount: NONE")
                print()
        else:
            print("NO selling plan groups attached to this product!")
    else:
        print("Product not found!")
else:
    print("No response from Shopify")

