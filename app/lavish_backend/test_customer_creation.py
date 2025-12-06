"""
Test creating a customer via the admin save flow
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from customers.models import ShopifyCustomer

def test_customer_creation():
    """Test creating a customer like the admin does"""
    
    print("\n" + "="*80)
    print("🧪 TESTING CUSTOMER CREATION")
    print("="*80 + "\n")
    
    # Create customer
    customer = ShopifyCustomer(
        email="test.customer@example.com",
        first_name="Test",
        last_name="Customer",
        phone="+61400000000",
        verified_email=True,
        accepts_marketing=True
    )
    
    print("1️⃣ Creating customer...")
    customer.save()
    print(f"   ✅ Customer created: {customer.full_name}")
    print(f"   ID: {customer.id}")
    print(f"   Shopify ID: {customer.shopify_id}")
    print(f"   Email: {customer.email}")
    print(f"   Created At: {customer.created_at}")
    print(f"   Needs Push: {customer.needs_shopify_push}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE - Customer creation working!")
    print("="*80 + "\n")
    
    # Clean up
    customer.delete()
    print("🧹 Test customer deleted\n")

if __name__ == "__main__":
    test_customer_creation()
