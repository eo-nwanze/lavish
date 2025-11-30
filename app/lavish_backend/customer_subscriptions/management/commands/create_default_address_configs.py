from django.core.management.base import BaseCommand
from customer_subscriptions.models import (
    CustomerSubscription, 
    SubscriptionAddress, 
    ProductShippingConfig
)
from customers.models import ShopifyCustomer
from products.models import ShopifyProduct
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create default subscription address configurations for all customers and products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating anything',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if configs already exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.create_default_subscription_addresses(dry_run, force)
        self.create_default_product_shipping_configs(dry_run, force)
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('✅ Default address configurations created successfully!')
            )

    def create_default_subscription_addresses(self, dry_run=False, force=False):
        """Create default subscription addresses for customers with subscriptions but no address"""
        
        self.stdout.write('\n📍 Creating default subscription addresses...')
        
        # Get customers with subscriptions but no subscription address
        customers_needing_addresses = ShopifyCustomer.objects.filter(
            subscriptions__isnull=False  # Has subscriptions
        ).exclude(
            subscription_address__isnull=False  # But no subscription address
        ).distinct()
        
        if force:
            # If force mode, get all customers with subscriptions
            customers_needing_addresses = ShopifyCustomer.objects.filter(
                subscriptions__isnull=False
            ).distinct()
            
        created_count = 0
        updated_count = 0
        
        for customer in customers_needing_addresses:
            try:
                # Get customer's default address from Shopify data
                default_address = None
                try:
                    if hasattr(customer, 'default_address') and customer.default_address:
                        default_address = customer.default_address
                    elif hasattr(customer, 'addresses') and customer.addresses.exists():
                        # Use first address if no default
                        default_address = customer.addresses.first()
                        if hasattr(default_address, '__dict__'):
                            # Convert model instance to dict
                            default_address = {
                                'first_name': default_address.first_name or customer.first_name or 'Customer',
                                'last_name': default_address.last_name or customer.last_name or '',
                                'company': getattr(default_address, 'company', ''),
                                'address1': default_address.address1 or '123 Main Street',
                                'address2': getattr(default_address, 'address2', ''),
                                'city': default_address.city or 'Sydney',
                                'province': default_address.province or 'NSW',
                                'country': default_address.country or 'Australia',
                                'zip': default_address.zip_code or '2000',
                                'phone': getattr(default_address, 'phone', ''),
                            }
                except Exception as e:
                    self.stdout.write(f'    Warning: Could not get address for {customer.email}: {e}')
                    default_address = None
                
                if not default_address and not dry_run:
                    # Create minimal address if no Shopify address available
                    default_address = {
                        'first_name': customer.first_name or 'Customer',
                        'last_name': customer.last_name or '',
                        'address1': '123 Main Street',  # Placeholder
                        'city': 'Sydney',
                        'province': 'NSW',
                        'country': 'Australia',
                        'zip': '2000',
                        'phone': '',
                    }
                    
                if not dry_run:
                    subscription_address, created = SubscriptionAddress.objects.get_or_create(
                        customer=customer,
                        defaults={
                            'first_name': default_address.get('first_name', customer.first_name or 'Customer'),
                            'last_name': default_address.get('last_name', customer.last_name or ''),
                            'company': default_address.get('company', ''),
                            'address1': default_address.get('address1', '123 Main Street'),
                            'address2': default_address.get('address2', ''),
                            'city': default_address.get('city', 'Sydney'),
                            'province': default_address.get('province', 'NSW'),
                            'country': default_address.get('country', 'Australia'),
                            'zip_code': default_address.get('zip', '2000'),
                            'phone': default_address.get('phone', ''),
                            'is_validated': False,
                            'validation_notes': 'Auto-created default address - needs validation',
                            'needs_shopify_sync': True,
                        }
                    )
                
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] Would create address for: {customer.email}')
                elif created:
                    created_count += 1
                    self.stdout.write(f'  ✅ Created address for: {customer.email}')
                elif force:
                    # Update existing address in force mode
                    for field, value in {
                        'first_name': default_address.get('first_name', customer.first_name),
                        'last_name': default_address.get('last_name', customer.last_name),
                        'company': default_address.get('company', ''),
                        'address1': default_address.get('address1', '123 Main Street'),
                        'address2': default_address.get('address2', ''),
                        'city': default_address.get('city', 'Sydney'),
                        'province': default_address.get('province', 'NSW'),
                        'country': default_address.get('country', 'Australia'),
                        'zip_code': default_address.get('zip', '2000'),
                        'phone': default_address.get('phone', ''),
                        'needs_shopify_sync': True,
                    }.items():
                        setattr(subscription_address, field, value)
                    subscription_address.save()
                    updated_count += 1
                    self.stdout.write(f'  ✅ Updated address for: {customer.email}')
                else:
                    self.stdout.write(f'  ➡️ Address exists for: {customer.email}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error creating address for {customer.email}: {e}')
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'📍 Subscription Addresses: {created_count} created, {updated_count} updated'
                )
            )

    def create_default_product_shipping_configs(self, dry_run=False, force=False):
        """Create default shipping configurations for products without config"""
        
        self.stdout.write('\n📦 Creating default product shipping configurations...')
        
        # Get products without shipping config
        products_needing_config = ShopifyProduct.objects.exclude(
            shipping_config__isnull=False
        )
        
        if force:
            # In force mode, get all products
            products_needing_config = ShopifyProduct.objects.all()
            
        created_count = 0
        updated_count = 0
        
        # Default shipping configuration
        default_config = {
            'cutoff_days': 7,
            'reminder_days': 14,
            'processing_days': 2,
            'estimated_transit_days': 5,
            'international_shipping': True,
            'restricted_countries': [],
            'special_handling': False,
            'handling_notes': 'Standard processing and shipping',
        }
        
        # Product-specific configurations
        product_specific_configs = {
            'book': {
                'cutoff_days': 10,
                'processing_days': 3,
                'estimated_transit_days': 3,
                'handling_notes': 'Books require careful packaging',
            },
            'sticker': {
                'cutoff_days': 5,
                'processing_days': 1,
                'estimated_transit_days': 3,
                'handling_notes': 'Small items - expedited processing',
            },
            'subscription': {
                'cutoff_days': 14,
                'reminder_days': 21,
                'processing_days': 5,
                'estimated_transit_days': 7,
                'handling_notes': 'Monthly subscription box - extended processing',
            },
        }
        
        for product in products_needing_config:
            try:
                # Determine product type for specific config
                product_type = 'standard'
                product_title_lower = product.title.lower()
                product_type_lower = (product.product_type or '').lower()
                
                if any(keyword in product_title_lower or keyword in product_type_lower 
                       for keyword in ['book', 'novel', 'magazine']):
                    product_type = 'book'
                elif any(keyword in product_title_lower or keyword in product_type_lower 
                        for keyword in ['sticker', 'decal', 'patch']):
                    product_type = 'sticker'
                elif any(keyword in product_title_lower or keyword in product_type_lower 
                        for keyword in ['subscription', 'box', 'monthly']):
                    product_type = 'subscription'
                
                # Get specific config or use default
                config = default_config.copy()
                if product_type in product_specific_configs:
                    config.update(product_specific_configs[product_type])
                
                if not dry_run:
                    shipping_config, created = ProductShippingConfig.objects.get_or_create(
                        product=product,
                        defaults=config
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            f'  ✅ Created {product_type} config for: {product.title[:50]}...'
                        )
                    elif force:
                        # Update existing config in force mode
                        for field, value in config.items():
                            setattr(shipping_config, field, value)
                        shipping_config.save()
                        updated_count += 1
                        self.stdout.write(
                            f'  ✅ Updated {product_type} config for: {product.title[:50]}...'
                        )
                    else:
                        self.stdout.write(
                            f'  ➡️ Config exists for: {product.title[:50]}...'
                        )
                else:
                    self.stdout.write(
                        f'  [DRY RUN] Would create {product_type} config for: {product.title[:50]}...'
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Error creating config for {product.title}: {e}'
                    )
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'📦 Product Shipping Configs: {created_count} created, {updated_count} updated'
                )
            )