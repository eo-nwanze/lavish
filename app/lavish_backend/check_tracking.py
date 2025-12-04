#!/usr/bin/env python
"""Check fulfillment order and tracking info counts"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from shipping.models import ShopifyFulfillmentOrder, FulfillmentTrackingInfo
from orders.models import ShopifyOrder

# Check counts
fulfillment_count = ShopifyFulfillmentOrder.objects.count()
tracking_count = FulfillmentTrackingInfo.objects.count()
order_count = ShopifyOrder.objects.count()

print(f"\n=== Database Status ===")
print(f"Orders: {order_count}")
print(f"Fulfillment Orders: {fulfillment_count}")
print(f"Tracking Info Records: {tracking_count}")

if fulfillment_count > 0:
    print(f"\n=== Sample Fulfillment Orders ===")
    for fo in ShopifyFulfillmentOrder.objects.all()[:5]:
        tracking = fo.tracking_info.count()
        print(f"  {fo.shopify_id}: {fo.status} - {tracking} tracking records")
        
    # Check if any have tracking
    with_tracking = ShopifyFulfillmentOrder.objects.filter(tracking_info__isnull=False).distinct().count()
    print(f"\nFulfillment orders with tracking: {with_tracking}/{fulfillment_count}")

if tracking_count > 0:
    print(f"\n=== Sample Tracking Info ===")
    for track in FulfillmentTrackingInfo.objects.all()[:5]:
        print(f"  {track.company}: {track.number}")
else:
    print("\n⚠️  No tracking info found - needs to be synced from Shopify")
