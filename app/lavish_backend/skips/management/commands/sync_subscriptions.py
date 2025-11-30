"""
Django management command to sync subscription data from Shopify

Usage:
    python manage.py sync_subscriptions
    python manage.py sync_subscriptions --customer-id 123456789
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
import os
from datetime import datetime, date

from skips.models import CustomerSubscription, SubscriptionSkipPolicy


class Command(BaseCommand):
    help = 'Sync subscription contracts from Shopify'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=str,
            help='Sync only subscriptions for specific Shopify customer ID'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of subscriptions to sync (default: 50)'
        )
    
    def handle(self, *args, **options):
        customer_id = options.get('customer_id')
        limit = options.get('limit')
        
        self.stdout.write(self.style.WARNING(
            '\n⚠️  Shopify GraphQL Integration Required\n'
        ))
        
        self.stdout.write(
            'This command requires Shopify Admin API access with subscription permissions.\n'
            'To implement:\n'
            '1. Add SHOPIFY_ADMIN_API_TOKEN to environment variables\n'
            '2. Use GraphQL query: subscriptionContracts\n'
            '3. Map Shopify data to CustomerSubscription model\n'
        )
        
        # Check for default skip policy
        default_policy = SubscriptionSkipPolicy.objects.filter(is_active=True).first()
        
        if not default_policy:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  No active skip policy found. Creating default policy...\n'
            ))
            default_policy = SubscriptionSkipPolicy.objects.create(
                name='Standard Skip Policy',
                max_skips_per_year=4,
                max_consecutive_skips=2,
                advance_notice_days=7,
                skip_fee=0.00,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created default skip policy: {default_policy.name}'
            ))
        
        # Example: Create sample subscription for testing
        self.stdout.write(self.style.WARNING(
            '\n📝 Creating sample subscription for testing...\n'
        ))
        
        sample_subscription, created = CustomerSubscription.objects.get_or_create(
            shopify_subscription_contract_id='gid://shopify/SubscriptionContract/SAMPLE123',
            defaults={
                'shopify_customer_id': 'gid://shopify/Customer/7380041244860',
                'customer_email': 'sample@example.com',
                'customer_name': 'Sample Customer',
                'subscription_name': 'Monthly Coffee Subscription',
                'billing_cycle': 'monthly',
                'status': 'active',
                'start_date': date.today(),
                'next_order_date': date.today().replace(day=15),
                'next_billing_date': date.today().replace(day=15),
                'product_price': 29.99,
                'shipping_price': 5.00,
                'total_price': 34.99,
                'currency_code': 'GBP',
                'skip_policy': default_policy,
                'skips_used_this_year': 0,
                'consecutive_skips': 0
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created sample subscription: {sample_subscription}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Sample subscription already exists: {sample_subscription}'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Sync process initialized. '
            f'Skip policy: {default_policy.name} '
            f'(Max {default_policy.max_skips_per_year} skips/year)\n'
        ))
        
        self.stdout.write(self.style.WARNING(
            '\n💡 Next Steps:\n'
            '1. Implement Shopify GraphQL queries in skips/shopify_client.py\n'
            '2. Add API token to environment variables\n'
            '3. Schedule this command to run periodically (e.g., daily cron job)\n'
            '4. Test skip functionality via API: POST /api/skips/skip/\n'
        ))
