#!/usr/bin/env python
"""Test script to verify subscription field fix"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customer_subscriptions.models import CustomerSubscription

# Test the field lookup
sub = CustomerSubscription.objects.filter(shopify_id__isnull=False).first()
if sub:
    print(f"✅ Subscription found using shopify_id field!")
    print(f"Customer: {sub.customer.full_name}")
    print(f"shopify_id: {sub.shopify_id}")
else:
    print("⚠️ No subscriptions with Shopify ID found")

# Test old field name (should fail)
try:
    sub_bad = CustomerSubscription.objects.filter(shopify_subscription_contract_id__isnull=False).first()
    print("❌ ERROR: Old field name still works (shouldn't happen)")
except Exception as e:
    print(f"✅ Old field name correctly fails: {type(e).__name__}")
