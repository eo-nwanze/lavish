"""
Test script to verify inventory auto-sync from Django admin to Shopify
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import ShopifyInventoryLevel, ShopifyInventoryItem, ShopifyLocation
from inventory.bidirectional_sync import InventoryBidirectionalSync
from django.utils import timezone

def test_inventory_sync():
    """Test updating inventory level and syncing to Shopify"""
    
    print("\n" + "="*80)
    print("🧪 TESTING INVENTORY LEVEL AUTO-SYNC TO SHOPIFY")
    print("="*80 + "\n")
    
    # Get the first inventory level to test with
    inventory_levels = ShopifyInventoryLevel.objects.select_related(
        'inventory_item', 'location'
    ).all()[:5]
    
    if not inventory_levels:
        print("❌ No inventory levels found in database")
        return
    
    print(f"Found {inventory_levels.count()} inventory levels\n")
    
    # Display current inventory levels
    print("📊 Current Inventory Levels:")
    print("-" * 80)
    for level in inventory_levels:
        item = level.inventory_item
        location = level.location
        print(f"\nInventory Item: {item.sku}")
        print(f"  - Shopify ID: {item.shopify_id}")
        print(f"  - Location: {location.name}")
        print(f"  - Location Shopify ID: {location.shopify_id}")
        print(f"  - Available: {level.available}")
        print(f"  - Needs Push: {level.needs_shopify_push}")
        print(f"  - Last Pushed: {level.last_pushed_to_shopify or 'Never'}")
        print(f"  - Push Error: {level.shopify_push_error or 'None'}")
    
    # Select first item to test
    test_level = inventory_levels[0]
    original_available = test_level.available
    
    print("\n" + "="*80)
    print(f"🎯 TESTING WITH: {test_level.inventory_item.sku}")
    print("="*80 + "\n")
    
    # Update available quantity
    new_quantity = 10  # Set to 10 for testing
    print(f"📝 Updating available quantity:")
    print(f"   Original: {original_available}")
    print(f"   New: {new_quantity}")
    
    test_level.available = new_quantity
    test_level.needs_shopify_push = True  # Flag for sync
    test_level.save()
    
    print(f"✅ Saved to Django (needs_shopify_push = True)\n")
    
    # Now manually trigger the sync to test
    print("🔄 Triggering Shopify sync...")
    sync_service = InventoryBidirectionalSync()
    result = sync_service.push_inventory_to_shopify(test_level)
    
    print("\n📊 SYNC RESULT:")
    print("-" * 80)
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('errors'):
        print(f"Errors: {result.get('errors')}")
    
    if result.get('adjustment_group'):
        print(f"Adjustment Group: {result.get('adjustment_group')}")
    
    # Check updated status
    test_level.refresh_from_db()
    print("\n📊 UPDATED STATUS:")
    print("-" * 80)
    print(f"Needs Push: {test_level.needs_shopify_push}")
    print(f"Last Pushed: {test_level.last_pushed_to_shopify}")
    print(f"Push Error: {test_level.shopify_push_error or 'None'}")
    
    print("\n" + "="*80)
    print("🏁 TEST COMPLETE")
    print("="*80 + "\n")
    
    # Instructions
    print("📋 NEXT STEPS:")
    print("1. Check Shopify admin to verify the quantity updated to 10")
    print("2. If it didn't sync, check the error message above")
    print("3. Try updating through Django admin to test save_formset()")
    print()

if __name__ == "__main__":
    test_inventory_sync()
