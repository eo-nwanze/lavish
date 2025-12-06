#!/usr/bin/env python
"""Test product creation from Django to Shopify"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ShopifyProduct
from django.utils import timezone

print("Creating test product via model (simulating admin)...")

# Create product using model directly
product = ShopifyProduct(
    title="Test 6 - Admin Fix Verification",
    description="Testing the fixed admin save logic",
    product_type="Test Product",
    vendor="Lavish",
    status="DRAFT"
)

# This should trigger the model's save() method which sets created_in_django=True
product.save()

print(f"\n✅ Product created in Django:")
print(f"   Title: {product.title}")
print(f"   shopify_id: {product.shopify_id}")
print(f"   created_in_django: {product.created_in_django}")
print(f"   needs_shopify_push: {product.needs_shopify_push}")
print(f"   created_at: {product.created_at}")

# Now test pushing to Shopify
from products.bidirectional_sync import ProductBidirectionalSync

print("\nPushing to Shopify...")
sync_service = ProductBidirectionalSync()
result = sync_service.push_product_to_shopify(product)

if result.get('success'):
    product.refresh_from_db()
    print(f"\n✅ Successfully pushed to Shopify!")
    print(f"   New shopify_id: {product.shopify_id}")
    print(f"   needs_shopify_push: {product.needs_shopify_push}")
else:
    print(f"\n❌ Push failed: {result.get('message', 'Unknown error')}")
