"""
Management command to test customer subscription bidirectional sync
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from customer_subscriptions.models import SellingPlan, CustomerSubscription
from customer_subscriptions.bidirectional_sync import subscription_sync
from customers.models import ShopifyCustomer
from products.models import ShopifyProduct


class Command(BaseCommand):
    help = 'Test customer subscription bidirectional sync'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-plan',
            action='store_true',
            help='Create a test selling plan in Django',
        )
        parser.add_argument(
            '--create-subscription',
            action='store_true',
            help='Create a test customer subscription in Django',
        )
        parser.add_argument(
            '--push-plan',
            type=int,
            help='Push selling plan to Shopify by ID',
        )
        parser.add_argument(
            '--push-subscription',
            type=int,
            help='Push subscription to Shopify by ID',
        )
        parser.add_argument(
            '--push-all-pending',
            action='store_true',
            help='Push all pending subscriptions',
        )

    def handle(self, *args, **options):
        if options['create_plan']:
            self.create_test_plan()
        elif options['create_subscription']:
            self.create_test_subscription()
        elif options['push_plan']:
            self.push_plan(options['push_plan'])
        elif options['push_subscription']:
            self.push_subscription(options['push_subscription'])
        elif options['push_all_pending']:
            self.push_all_pending()
        else:
            self.stdout.write(self.style.WARNING('No action specified. Use --create-plan, --create-subscription, --push-plan, --push-subscription, or --push-all-pending'))

    def create_test_plan(self):
        """Create a test selling plan in Django"""
        self.stdout.write(self.style.SUCCESS('Creating test selling plan in Django...'))
        
        plan = SellingPlan.objects.create(
            name="Monthly Lavish Box",
            description="Get a curated box of luxury items every month with 10% discount",
            billing_policy='RECURRING',
            billing_interval='MONTH',
            billing_interval_count=1,
            price_adjustment_type='PERCENTAGE',
            price_adjustment_value=10.00,
            delivery_policy='RECURRING',
            delivery_interval='MONTH',
            delivery_interval_count=1,
            is_active=True,
            created_in_django=True,
            needs_shopify_push=True,
        )
        
        # Associate with products if any exist
        products = ShopifyProduct.objects.filter(status='ACTIVE')[:3]
        if products.exists():
            plan.products.set(products)
            self.stdout.write(self.style.SUCCESS(f'   - Associated with {products.count()} products'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created test selling plan: {plan.name} (ID: {plan.id})'))
        self.stdout.write(self.style.SUCCESS(f'   - Billing: Every {plan.billing_interval_count} {plan.billing_interval}'))
        self.stdout.write(self.style.SUCCESS(f'   - Discount: {plan.price_adjustment_value}%'))
        self.stdout.write(self.style.SUCCESS(f'   - Marked for push to Shopify'))
        self.stdout.write(self.style.WARNING(f'\nTo push this plan to Shopify, run:'))
        self.stdout.write(self.style.WARNING(f'   python manage.py test_customer_subscriptions --push-plan {plan.id}'))

    def create_test_subscription(self):
        """Create a test customer subscription in Django"""
        self.stdout.write(self.style.SUCCESS('Creating test customer subscription in Django...'))
        
        # Get a customer
        customer = ShopifyCustomer.objects.filter(email__isnull=False).first()
        if not customer:
            self.stdout.write(self.style.ERROR('❌ No customers found. Please import customers from Shopify first.'))
            return
        
        # Get a selling plan
        plan = SellingPlan.objects.first()
        if not plan:
            self.stdout.write(self.style.WARNING('No selling plan found. Creating one...'))
            self.create_test_plan()
            plan = SellingPlan.objects.first()
        
        # Get a product variant for line items
        product = ShopifyProduct.objects.filter(status='ACTIVE', variants__isnull=False).first()
        line_items = []
        if product and product.variants.exists():
            variant = product.variants.first()
            line_items = [{
                "variant_id": variant.shopify_id,
                "product_title": product.title,
                "variant_title": variant.title,
                "quantity": 1,
                "price": str(variant.price),
                "selling_plan_id": plan.shopify_id if plan and plan.shopify_id else ""
            }]
        
        # Create subscription
        subscription = CustomerSubscription.objects.create(
            customer=customer,
            selling_plan=plan,
            status='ACTIVE',
            currency='USD',
            next_billing_date=date.today() + timedelta(days=30),
            billing_policy_interval='MONTH',
            billing_policy_interval_count=1,
            next_delivery_date=date.today() + timedelta(days=30),
            delivery_policy_interval='MONTH',
            delivery_policy_interval_count=1,
            line_items=line_items,
            total_price=29.99,
            delivery_address={
                "address1": "123 Main St",
                "city": "New York",
                "province": "NY",
                "country": "United States",
                "zip": "10001"
            },
            created_in_django=True,
            needs_shopify_push=True,
        )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created test subscription (ID: {subscription.id})'))
        self.stdout.write(self.style.SUCCESS(f'   - Customer: {customer.first_name} {customer.last_name} ({customer.email})'))
        self.stdout.write(self.style.SUCCESS(f'   - Plan: {plan.name if plan else "None"}'))
        self.stdout.write(self.style.SUCCESS(f'   - Status: {subscription.status}'))
        self.stdout.write(self.style.SUCCESS(f'   - Next Billing: {subscription.next_billing_date}'))
        self.stdout.write(self.style.SUCCESS(f'   - Total Price: ${subscription.total_price}'))
        self.stdout.write(self.style.SUCCESS(f'   - Marked for push to Shopify'))
        self.stdout.write(self.style.WARNING(f'\nTo push this subscription to Shopify, run:'))
        self.stdout.write(self.style.WARNING(f'   python manage.py test_customer_subscriptions --push-subscription {subscription.id}'))

    def push_plan(self, plan_id):
        """Push a selling plan to Shopify"""
        try:
            plan = SellingPlan.objects.get(id=plan_id)
            self.stdout.write(self.style.SUCCESS(f'Pushing selling plan to Shopify: {plan.name}'))
            
            result = subscription_sync.create_selling_plan_in_shopify(plan)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(f'✅ {result.get("message")}'))
                if 'shopify_id' in result:
                    self.stdout.write(self.style.SUCCESS(f'   Shopify ID: {result["shopify_id"]}'))
                if 'group_id' in result:
                    self.stdout.write(self.style.SUCCESS(f'   Group ID: {result["group_id"]}'))
                
                plan.refresh_from_db()
                self.stdout.write(self.style.SUCCESS(f'   Needs Push: {plan.needs_shopify_push}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {result.get("message")}'))
                if 'errors' in result:
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f'   - {error}'))
        
        except SellingPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Selling plan with ID {plan_id} not found'))

    def push_subscription(self, subscription_id):
        """Push a subscription to Shopify"""
        try:
            subscription = CustomerSubscription.objects.get(id=subscription_id)
            self.stdout.write(self.style.SUCCESS(f'Pushing subscription to Shopify for customer: {subscription.customer.email}'))
            
            result = subscription_sync.create_subscription_in_shopify(subscription)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(f'✅ {result.get("message")}'))
                if 'shopify_id' in result:
                    self.stdout.write(self.style.SUCCESS(f'   Shopify ID: {result["shopify_id"]}'))
                
                subscription.refresh_from_db()
                self.stdout.write(self.style.SUCCESS(f'   Status: {subscription.status}'))
                self.stdout.write(self.style.SUCCESS(f'   Needs Push: {subscription.needs_shopify_push}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {result.get("message")}'))
                if 'errors' in result:
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f'   - {error}'))
        
        except CustomerSubscription.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Subscription with ID {subscription_id} not found'))

    def push_all_pending(self):
        """Push all pending subscriptions"""
        self.stdout.write(self.style.SUCCESS('Pushing all pending subscriptions to Shopify...'))
        
        results = subscription_sync.sync_pending_subscriptions()
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Results:'))
        self.stdout.write(self.style.SUCCESS(f'   Total: {results["total"]}'))
        self.stdout.write(self.style.SUCCESS(f'   ✅ Successful: {results["successful"]}'))
        
        if results["failed"] > 0:
            self.stdout.write(self.style.ERROR(f'   ❌ Failed: {results["failed"]}'))
            for error in results["errors"]:
                self.stdout.write(self.style.ERROR(f'      - {error["customer"]}: {error["error"]}'))
