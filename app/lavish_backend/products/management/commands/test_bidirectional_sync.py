"""
Management command to test bidirectional product sync
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from products.models import ShopifyProduct, ShopifyProductVariant
from products.bidirectional_sync import bidirectional_sync


class Command(BaseCommand):
    help = 'Test bidirectional product sync - create a test product in Django and push to Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test',
            action='store_true',
            help='Create a test product in Django',
        )
        parser.add_argument(
            '--push-all-pending',
            action='store_true',
            help='Push all products marked as needs_shopify_push',
        )
        parser.add_argument(
            '--product-id',
            type=int,
            help='Push specific product by ID',
        )

    def handle(self, *args, **options):
        if options['create_test']:
            self.create_test_product()
        elif options['push_all_pending']:
            self.push_all_pending()
        elif options['product_id']:
            self.push_specific_product(options['product_id'])
        else:
            self.stdout.write(self.style.WARNING('No action specified. Use --create-test, --push-all-pending, or --product-id'))

    def create_test_product(self):
        """Create a test product in Django"""
        self.stdout.write(self.style.SUCCESS('Creating test product in Django...'))
        
        # Create product
        product = ShopifyProduct.objects.create(
            title=f"Test Product from Django {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            description="<p>This is a test product created in Django admin and pushed to Shopify using bidirectional sync.</p>",
            vendor="Lavish Library",
            product_type="Test Products",
            status="DRAFT",
            tags=["test", "django-created", "bidirectional-sync"],
            created_at=timezone.now(),
            updated_at=timezone.now(),
            created_in_django=True,
            needs_shopify_push=True,
        )
        
        # Create a variant
        variant = ShopifyProductVariant.objects.create(
            product=product,
            shopify_id="",  # Will be filled when pushed to Shopify
            title="Default",
            price="29.99",
            sku="TEST-DJANGO-001",
            inventory_quantity=10,
            available=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created test product: {product.title} (ID: {product.id})'))
        self.stdout.write(self.style.SUCCESS(f'   - Variant: {variant.title} - ${variant.price}'))
        self.stdout.write(self.style.SUCCESS(f'   - Marked for push to Shopify'))
        self.stdout.write(self.style.WARNING(f'\nTo push this product to Shopify, run:'))
        self.stdout.write(self.style.WARNING(f'   python manage.py test_bidirectional_sync --product-id {product.id}'))
        self.stdout.write(self.style.WARNING(f'Or use Django admin action: "Push to Shopify"'))

    def push_specific_product(self, product_id):
        """Push a specific product to Shopify"""
        try:
            product = ShopifyProduct.objects.get(id=product_id)
            self.stdout.write(self.style.SUCCESS(f'Pushing product to Shopify: {product.title}'))
            
            result = bidirectional_sync.push_product_to_shopify(product)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(f'✅ {result.get("message")}'))
                if 'shopify_id' in result:
                    self.stdout.write(self.style.SUCCESS(f'   Shopify ID: {result["shopify_id"]}'))
                
                # Refresh from database
                product.refresh_from_db()
                self.stdout.write(self.style.SUCCESS(f'   Handle: {product.handle}'))
                self.stdout.write(self.style.SUCCESS(f'   Status: {product.sync_status}'))
                self.stdout.write(self.style.SUCCESS(f'   Needs Push: {product.needs_shopify_push}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {result.get("message")}'))
                if 'errors' in result:
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f'   - {error}'))
        
        except ShopifyProduct.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Product with ID {product_id} not found'))

    def push_all_pending(self):
        """Push all products marked for push"""
        self.stdout.write(self.style.SUCCESS('Pushing all pending products to Shopify...'))
        
        results = bidirectional_sync.sync_pending_products()
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Results:'))
        self.stdout.write(self.style.SUCCESS(f'   Total: {results["total"]}'))
        self.stdout.write(self.style.SUCCESS(f'   ✅ Successful: {results["successful"]}'))
        
        if results["failed"] > 0:
            self.stdout.write(self.style.ERROR(f'   ❌ Failed: {results["failed"]}'))
            for error in results["errors"]:
                self.stdout.write(self.style.ERROR(f'      - Product {error["product_id"]} ({error["product_title"]}): {error["error"]}'))
