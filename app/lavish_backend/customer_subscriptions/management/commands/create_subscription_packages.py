"""
Management command to create multiple subscription packages
with different product types
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from products.models import ShopifyProduct
from customer_subscriptions.models import SellingPlan
from customer_subscriptions.bidirectional_sync import SubscriptionBidirectionalSync


class Command(BaseCommand):
    help = 'Create subscription packages for books, stickers, and mixed products'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Creating Subscription Packages")
        self.stdout.write("="*60 + "\n")

        # Create subscription packages
        packages = self.create_packages()
        
        self.stdout.write(f"\n✅ Created {len(packages)} subscription packages")
        self.stdout.write("\nTo push these to Shopify, run:")
        for package in packages:
            self.stdout.write(f"   python manage.py test_customer_subscriptions --push-plan {package.id}")
        
        self.stdout.write("\n" + "="*60 + "\n")

    def create_packages(self):
        """Create different subscription packages"""
        packages = []
        
        # Package 1: Monthly Book Box (15% off)
        self.stdout.write("\n📚 Creating: Monthly Book Box...")
        book_plan = SellingPlan.objects.create(
            name="Monthly Book Box",
            description="Get a curated special edition book delivered monthly with 15% off",
            billing_interval="MONTH",
            billing_interval_count=1,
            delivery_interval="MONTH",
            delivery_interval_count=1,
            price_adjustment_type="PERCENTAGE",
            price_adjustment_value=15.0,
            is_active=True,
            created_in_django=True,
            needs_shopify_push=True
        )
        
        # Associate with book products
        books = ShopifyProduct.objects.filter(
            product_type__iexact="Book",
            status="ACTIVE"
        )[:5]  # First 5 books
        
        for book in books:
            book_plan.products.add(book)
        
        self.stdout.write(f"   ✓ Associated with {books.count()} book products")
        packages.append(book_plan)
        
        # Package 2: Sticker Club (20% off, bi-monthly)
        self.stdout.write("\n🎨 Creating: Bi-Monthly Sticker Club...")
        sticker_plan = SellingPlan.objects.create(
            name="Bi-Monthly Sticker Club",
            description="Receive exclusive stickers every 2 months with 20% savings",
            billing_interval="MONTH",
            billing_interval_count=2,
            delivery_interval="MONTH",
            delivery_interval_count=2,
            price_adjustment_type="PERCENTAGE",
            price_adjustment_value=20.0,
            is_active=True,
            created_in_django=True,
            needs_shopify_push=True
        )
        
        # Associate with sticker products
        stickers = ShopifyProduct.objects.filter(
            title__icontains="sticker",
            status="ACTIVE"
        )[:8]  # First 8 stickers
        
        for sticker in stickers:
            sticker_plan.products.add(sticker)
        
        self.stdout.write(f"   ✓ Associated with {stickers.count()} sticker products")
        packages.append(sticker_plan)
        
        # Package 3: Weekly Romance Bundle (10% off)
        self.stdout.write("\n💝 Creating: Weekly Romance Bundle...")
        romance_plan = SellingPlan.objects.create(
            name="Weekly Romance Bundle",
            description="Weekly delivery of romance-themed items with 10% discount",
            billing_interval="WEEK",
            billing_interval_count=1,
            delivery_interval="WEEK",
            delivery_interval_count=1,
            price_adjustment_type="PERCENTAGE",
            price_adjustment_value=10.0,
            is_active=True,
            created_in_django=True,
            needs_shopify_push=True
        )
        
        # Associate with romance-related products
        romance_products = ShopifyProduct.objects.filter(
            status="ACTIVE"
        ).filter(
            title__icontains="romance"
        ) | ShopifyProduct.objects.filter(
            status="ACTIVE",
            title__icontains="Mafia Romance"
        )
        
        for product in romance_products[:6]:
            romance_plan.products.add(product)
        
        self.stdout.write(f"   ✓ Associated with {romance_products[:6].count()} romance products")
        packages.append(romance_plan)
        
        # Package 4: Quarterly Collector's Box (25% off)
        self.stdout.write("\n🎁 Creating: Quarterly Collector's Box...")
        collectors_plan = SellingPlan.objects.create(
            name="Quarterly Collector's Box",
            description="Premium quarterly box with special editions, stickers, and exclusive items - 25% off",
            billing_interval="MONTH",
            billing_interval_count=3,
            delivery_interval="MONTH",
            delivery_interval_count=3,
            price_adjustment_type="PERCENTAGE",
            price_adjustment_value=25.0,
            is_active=True,
            created_in_django=True,
            needs_shopify_push=True
        )
        
        # Associate with mix of products
        mixed_products = list(books[:2]) + list(stickers[:3])
        for product in mixed_products:
            collectors_plan.products.add(product)
        
        self.stdout.write(f"   ✓ Associated with {len(mixed_products)} mixed products")
        packages.append(collectors_plan)
        
        # Package 5: Fantasy Lover's Monthly (12% off)
        self.stdout.write("\n🐉 Creating: Fantasy Lover's Monthly...")
        fantasy_plan = SellingPlan.objects.create(
            name="Fantasy Lover's Monthly",
            description="Monthly fantasy book and themed accessories with 12% discount",
            billing_interval="MONTH",
            billing_interval_count=1,
            delivery_interval="MONTH",
            delivery_interval_count=1,
            price_adjustment_type="PERCENTAGE",
            price_adjustment_value=12.0,
            is_active=True,
            created_in_django=True,
            needs_shopify_push=True
        )
        
        # Associate with fantasy/dragon themed products
        fantasy_products = ShopifyProduct.objects.filter(
            status="ACTIVE"
        ).filter(
            title__icontains="Dragon"
        ) | ShopifyProduct.objects.filter(
            status="ACTIVE",
            title__icontains="Fae"
        )
        
        for product in fantasy_products[:5]:
            fantasy_plan.products.add(product)
        
        self.stdout.write(f"   ✓ Associated with {fantasy_products[:5].count()} fantasy products")
        packages.append(fantasy_plan)
        
        return packages
