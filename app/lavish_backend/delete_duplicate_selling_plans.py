"""
Delete Duplicate Selling Plan Groups
=====================================

This will delete the older duplicate selling plan groups,
keeping only the newest instance of each.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import json


def delete_duplicate_selling_plans():
    """Delete duplicate selling plan groups, keep only newest"""
    
    print("=" * 80)
    print("DELETE DUPLICATE SELLING PLAN GROUPS")
    print("=" * 80)
    
    # List of duplicate group IDs to delete (keep newest, delete older)
    duplicates_to_delete = [
        # Monthly Lavish Box - delete 2 older instances
        ("gid://shopify/SellingPlanGroup/4935221342", "Monthly Lavish Box", "2025-12-06T08:52:46Z"),
        ("gid://shopify/SellingPlanGroup/4919394398", "Monthly Lavish Box", "2025-11-29T14:55:35Z"),
        
        # Monthly Book Box - delete 2 older instances
        ("gid://shopify/SellingPlanGroup/4935188574", "Monthly Book Box", "2025-12-06T08:52:44Z"),
        ("gid://shopify/SellingPlanGroup/4919427166", "Monthly Book Box", "2025-11-29T15:04:59Z"),
        
        # Bi-Monthly Sticker Club - delete 2 older instances
        ("gid://shopify/SellingPlanGroup/4935155806", "Bi-Monthly Sticker Club", "2025-12-06T08:52:43Z"),
        ("gid://shopify/SellingPlanGroup/4919459934", "Bi-Monthly Sticker Club", "2025-11-29T15:05:09Z"),
        
        # Weekly Romance Bundle - delete 2 older instances
        ("gid://shopify/SellingPlanGroup/4935123038", "Weekly Romance Bundle", "2025-12-06T08:52:41Z"),
        ("gid://shopify/SellingPlanGroup/4919492702", "Weekly Romance Bundle", "2025-11-29T15:05:11Z"),
        
        # Quarterly Collector's Box - delete 2 older instances
        ("gid://shopify/SellingPlanGroup/4935090270", "Quarterly Collector's Box", "2025-12-06T08:52:39Z"),
        ("gid://shopify/SellingPlanGroup/4919525470", "Quarterly Collector's Box", "2025-11-29T15:05:13Z"),
        
        # Fantasy Lover's Monthly - delete 2 older instances
        ("gid://shopify/SellingPlanGroup/4935057502", "Fantasy Lover's Monthly", "2025-12-06T08:52:36Z"),
        ("gid://shopify/SellingPlanGroup/4919558238", "Fantasy Lover's Monthly", "2025-11-29T15:05:15Z"),
    ]
    
    print(f"\n⚠️ WARNING: About to delete {len(duplicates_to_delete)} duplicate selling plan groups!")
    print("This will keep only the NEWEST instance of each plan.")
    print("\nDuplicates to delete:")
    
    for group_id, name, created in duplicates_to_delete:
        print(f"  - {name} (created {created})")
    
    print("\n" + "=" * 80)
    response = input("Proceed with deletion? (yes/no): ")
    
    if response.lower() != 'yes':
        print("\n❌ Cancelled. No changes made.")
        return
    
    client = EnhancedShopifyAPIClient()
    
    mutation = """
    mutation sellingPlanGroupDelete($id: ID!) {
      sellingPlanGroupDelete(id: $id) {
        deletedSellingPlanGroupId
        userErrors {
          field
          message
        }
      }
    }
    """
    
    success_count = 0
    error_count = 0
    errors = []
    
    print("\n" + "=" * 80)
    print("DELETING DUPLICATES...")
    print("=" * 80)
    
    for group_id, name, created in duplicates_to_delete:
        print(f"\n🗑️  Deleting: {name} ({created})")
        print(f"   ID: {group_id}")
        
        result = client.execute_graphql_query(mutation, {"id": group_id})
        
        if "errors" in result:
            print(f"   ❌ GraphQL Error: {result['errors']}")
            error_count += 1
            errors.append({"name": name, "error": result["errors"]})
            continue
        
        delete_data = result.get("data", {}).get("sellingPlanGroupDelete", {})
        user_errors = delete_data.get("userErrors", [])
        
        if user_errors:
            print(f"   ❌ Validation Error: {user_errors}")
            error_count += 1
            errors.append({"name": name, "error": user_errors})
        else:
            deleted_id = delete_data.get("deletedSellingPlanGroupId")
            print(f"   ✅ Deleted: {deleted_id}")
            success_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("DELETION SUMMARY")
    print("=" * 80)
    
    print(f"\n  ✅ Successfully deleted: {success_count}")
    print(f"  ❌ Failed: {error_count}")
    
    if errors:
        print("\n  Errors:")
        for err in errors:
            print(f"    - {err['name']}: {err['error']}")
    
    if success_count > 0:
        print("\n🎉 Duplicates removed! Now customers will see only one instance of each plan.")
        print("   Refresh your product page to verify.")


if __name__ == '__main__':
    delete_duplicate_selling_plans()

