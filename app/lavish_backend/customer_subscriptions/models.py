"""
Customer Subscription Models with Bidirectional Shopify Sync

Manages customer subscriptions that sync with Shopify Subscription Contracts.
Supports creating subscriptions in Django and pushing to Shopify, or importing from Shopify.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import json


class SellingPlan(models.Model):
    """
    Selling Plan (Subscription Plan) - Product subscription configurations
    Can be created in Django and pushed to Shopify
    """
    
    BILLING_POLICY_CHOICES = [
        ('RECURRING', 'Recurring'),
        ('ON_PURCHASE', 'On Purchase'),
    ]
    
    INTERVAL_CHOICES = [
        ('DAY', 'Day'),
        ('WEEK', 'Week'),
        ('MONTH', 'Month'),
        ('YEAR', 'Year'),
    ]
    
    DELIVERY_POLICY_CHOICES = [
        ('RECURRING', 'Recurring'),
        ('ON_PURCHASE', 'On Purchase'),
    ]
    
    # Shopify Integration
    shopify_id = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Shopify SellingPlan GID")
    shopify_selling_plan_group_id = models.CharField(max_length=255, blank=True, help_text="Parent SellingPlanGroup GID")
    
    # Basic Info
    name = models.CharField(max_length=255, help_text="Plan name (e.g., 'Monthly Box')")
    description = models.TextField(blank=True, help_text="Plan description")
    
    # Billing Configuration
    billing_policy = models.CharField(max_length=20, choices=BILLING_POLICY_CHOICES, default='RECURRING')
    billing_interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='MONTH')
    billing_interval_count = models.IntegerField(default=1, validators=[MinValueValidator(1)], help_text="e.g., 1 for monthly, 3 for quarterly")
    billing_anchors = models.JSONField(default=list, blank=True, help_text="Billing anchor days")
    
    # Pricing
    price_adjustment_type = models.CharField(max_length=20, default='PERCENTAGE', choices=[
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED_AMOUNT', 'Fixed Amount Discount'),
        ('PRICE', 'Fixed Price'),
    ])
    price_adjustment_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount/price value")
    
    # Delivery Configuration
    delivery_policy = models.CharField(max_length=20, choices=DELIVERY_POLICY_CHOICES, default='RECURRING')
    delivery_interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='MONTH')
    delivery_interval_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    delivery_anchors = models.JSONField(default=list, blank=True, help_text="Delivery anchor days")
    
    # Fulfillment Options
    fulfillment_exact_time = models.BooleanField(default=False, help_text="Fulfill at exact time")
    fulfillment_intent = models.CharField(max_length=50, default='FULFILLMENT_BEGIN', choices=[
        ('FULFILLMENT_BEGIN', 'Fulfillment Begin'),
        ('FULFILLMENT_EXACT_TIME', 'Fulfillment Exact Time'),
    ])
    
    # Product Association
    products = models.ManyToManyField('products.ShopifyProduct', related_name='selling_plans', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Bidirectional Sync Tracking
    created_in_django = models.BooleanField(default=False, help_text="True if created in Django (not imported)")
    needs_shopify_push = models.BooleanField(default=False, help_text="True if needs push to Shopify")
    shopify_push_error = models.TextField(blank=True, help_text="Last push error message")
    last_pushed_to_shopify = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Selling Plan'
        verbose_name_plural = 'Selling Plans'
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['needs_shopify_push']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.billing_interval_count} {self.billing_interval})"
    
    def save(self, *args, **kwargs):
        """Auto-track changes for bidirectional sync"""
        if not self.pk and not self.shopify_id:
            self.created_in_django = True
            self.needs_shopify_push = True
        elif self.pk and self.shopify_id:
            try:
                old = SellingPlan.objects.get(pk=self.pk)
                if (old.name != self.name or old.price_adjustment_value != self.price_adjustment_value or
                    old.billing_interval != self.billing_interval or old.billing_interval_count != self.billing_interval_count):
                    self.needs_shopify_push = True
            except SellingPlan.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class SubscriptionAddress(models.Model):
    """
    Primary Subscription Address - Customer's default subscription delivery address
    Changes propagate to all unshipped orders automatically
    """
    
    customer = models.OneToOneField('customers.ShopifyCustomer', on_delete=models.CASCADE, related_name='subscription_address')
    
    # Address Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Australia')
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address Validation
    is_validated = models.BooleanField(default=False, help_text="Address validated by shipping carrier")
    validation_notes = models.TextField(blank=True, help_text="Address validation notes or corrections")
    
    # Change Tracking
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True, help_text="Who updated the address")
    
    # Sync with Shopify
    needs_shopify_sync = models.BooleanField(default=True, help_text="Address needs sync to Shopify subscriptions")
    last_shopify_sync = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Subscription Address'
        verbose_name_plural = 'Subscription Addresses'
    
    def __str__(self):
        return f"{self.customer.email} - {self.address1}, {self.city}"
    
    def get_full_address(self):
        """Return formatted full address"""
        lines = [f"{self.first_name} {self.last_name}"]
        if self.company:
            lines.append(self.company)
        lines.append(self.address1)
        if self.address2:
            lines.append(self.address2)
        lines.append(f"{self.city}, {self.province} {self.zip_code}")
        lines.append(self.country)
        return "\n".join(lines)
    
    def save(self, *args, **kwargs):
        """Auto-propagate address changes to unshipped orders"""
        is_update = bool(self.pk)
        super().save(*args, **kwargs)
        
        if is_update:
            # Propagate to unshipped subscription orders
            self._propagate_to_unshipped_orders()
            self.needs_shopify_sync = True
            super().save(update_fields=['needs_shopify_sync'])
    
    def _propagate_to_unshipped_orders(self):
        """Propagate address changes to unshipped orders for this customer"""
        from orders.models import ShopifyOrder, ShopifyOrderAddress
        
        unshipped_orders = ShopifyOrder.objects.filter(
            customer=self.customer,
            fulfillment_status__in=['null', 'partial']  # Unfulfilled or partially fulfilled
        )
        
        for order in unshipped_orders:
            # Check if order has address override
            if not hasattr(order, 'address_override'):
                # Update shipping address if no override exists
                shipping_address, created = ShopifyOrderAddress.objects.get_or_create(
                    order=order,
                    address_type='shipping',
                    defaults={
                        'first_name': self.first_name,
                        'last_name': self.last_name,
                        'company': self.company,
                        'address1': self.address1,
                        'address2': self.address2,
                        'city': self.city,
                        'province': self.province,
                        'country': self.country,
                        'zip_code': self.zip_code,
                        'phone': self.phone,
                    }
                )
                
                if not created:
                    # Update existing address
                    shipping_address.first_name = self.first_name
                    shipping_address.last_name = self.last_name
                    shipping_address.company = self.company
                    shipping_address.address1 = self.address1
                    shipping_address.address2 = self.address2
                    shipping_address.city = self.city
                    shipping_address.province = self.province
                    shipping_address.country = self.country
                    shipping_address.zip_code = self.zip_code
                    shipping_address.phone = self.phone
                    shipping_address.save()


class OrderAddressOverride(models.Model):
    """
    Per-Order Address Override - Override shipping address for specific delivery only
    Does not affect primary subscription address
    """
    
    order = models.OneToOneField('orders.ShopifyOrder', on_delete=models.CASCADE, related_name='address_override')
    
    # Override Address Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Australia')
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)
    
    # Override Details
    reason = models.CharField(max_length=255, blank=True, help_text="Reason for address override")
    is_temporary = models.BooleanField(default=True, help_text="True for one-time override, False for permanent change")
    
    # Tracking
    created_by = models.CharField(max_length=100, help_text="Who created this override")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Sync Status
    needs_shopify_sync = models.BooleanField(default=True)
    last_shopify_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order Address Override'
        verbose_name_plural = 'Order Address Overrides'
    
    def __str__(self):
        return f"Override for {self.order.name} - {self.address1}, {self.city}"
    
    def get_full_address(self):
        """Return formatted full address"""
        lines = [f"{self.first_name} {self.last_name}"]
        if self.company:
            lines.append(self.company)
        lines.append(self.address1)
        if self.address2:
            lines.append(self.address2)
        lines.append(f"{self.city}, {self.province} {self.zip_code}")
        lines.append(self.country)
        return "\n".join(lines)


class ProductShippingConfig(models.Model):
    """
    Per-Product Shipping Configuration
    Configurable cutoff days and shipping settings per product
    """
    
    product = models.OneToOneField('products.ShopifyProduct', on_delete=models.CASCADE, related_name='shipping_config')
    
    # Cutoff Configuration
    cutoff_days = models.IntegerField(default=7, help_text="Days before shipping when orders are cut off")
    reminder_days = models.IntegerField(default=14, help_text="Days before cutoff to send reminder (default: 14)")
    
    # Shipping Details
    processing_days = models.IntegerField(default=2, help_text="Days needed to process/prepare order")
    estimated_transit_days = models.IntegerField(default=5, help_text="Estimated shipping transit time")
    
    # Special Instructions
    special_handling = models.BooleanField(default=False, help_text="Requires special handling")
    handling_notes = models.TextField(blank=True, help_text="Special handling instructions")
    
    # Restrictions
    international_shipping = models.BooleanField(default=True, help_text="Available for international shipping")
    restricted_countries = models.JSONField(default=list, blank=True, help_text="Country codes where shipping is restricted")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Shipping Config'
        verbose_name_plural = 'Product Shipping Configs'
    
    def __str__(self):
        return f"{self.product.title} - {self.cutoff_days} day cutoff"
    
    def get_cutoff_date(self, shipping_date):
        """Calculate cutoff date based on shipping date"""
        from datetime import timedelta
        return shipping_date - timedelta(days=self.cutoff_days)
    
    def get_reminder_date(self, cutoff_date):
        """Calculate reminder date based on cutoff date"""
        from datetime import timedelta
        return cutoff_date - timedelta(days=self.reminder_days)


class ShippingCutoffLog(models.Model):
    """
    Log of cutoff notifications and reminders sent to customers
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('REMINDER', 'Cutoff Reminder'),
        ('CUTOFF', 'Cutoff Notification'),
        ('SHIPPED', 'Shipping Confirmation'),
    ]
    
    order = models.ForeignKey('orders.ShopifyOrder', on_delete=models.CASCADE, related_name='cutoff_logs')
    customer = models.ForeignKey('customers.ShopifyCustomer', on_delete=models.CASCADE, related_name='cutoff_notifications')
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    cutoff_date = models.DateField(help_text="The cutoff date for this notification")
    
    # Notification Details
    sent_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    
    # Content
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    
    # Status
    delivery_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ])
    
    class Meta:
        verbose_name = 'Shipping Cutoff Log'
        verbose_name_plural = 'Shipping Cutoff Logs'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.notification_type} for {self.order.name} - {self.cutoff_date}"


class CustomerSubscription(models.Model):
    """
    Customer Subscription - Maps to Shopify SubscriptionContract
    Bidirectional sync enabled
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('FAILED', 'Failed'),
    ]
    
    # Shopify Integration
    shopify_id = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Shopify SubscriptionContract GID")
    
    # Customer Reference
    customer = models.ForeignKey('customers.ShopifyCustomer', on_delete=models.CASCADE, related_name='subscriptions', help_text="Customer who owns this subscription")
    
    # Selling Plan Reference
    selling_plan = models.ForeignKey(SellingPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_subscriptions')
    
    # Subscription Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    currency = models.CharField(max_length=3, default='USD')
    
    # Billing & Delivery
    next_billing_date = models.DateField(null=True, blank=True, help_text="Next billing date")
    billing_policy_interval = models.CharField(max_length=10, default='MONTH')
    billing_policy_interval_count = models.IntegerField(default=1)
    
    next_delivery_date = models.DateField(null=True, blank=True, help_text="Next delivery date")
    delivery_policy_interval = models.CharField(max_length=10, default='MONTH')
    delivery_policy_interval_count = models.IntegerField(default=1)
    
    # Pricing
    line_items = models.JSONField(default=list, help_text="Subscription line items (products)")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Delivery Address
    delivery_address = models.JSONField(default=dict, blank=True, help_text="Delivery address details")
    
    # Payment Method
    payment_method_id = models.CharField(max_length=255, blank=True, help_text="Shopify payment method ID")
    
    # Contract Details
    contract_created_at = models.DateTimeField(null=True, blank=True, help_text="When subscription was created in Shopify")
    contract_updated_at = models.DateTimeField(null=True, blank=True, help_text="Last update in Shopify")
    
    # Trial Period
    trial_end_date = models.DateField(null=True, blank=True, help_text="Trial period end date")
    
    # Cycle Info
    billing_cycle_count = models.IntegerField(default=0, help_text="Number of billing cycles completed")
    total_cycles = models.IntegerField(null=True, blank=True, help_text="Total cycles (null = infinite)")
    
    # Bidirectional Sync Tracking
    created_in_django = models.BooleanField(default=False, help_text="True if created in Django")
    needs_shopify_push = models.BooleanField(default=False, help_text="True if needs push to Shopify")
    shopify_push_error = models.TextField(blank=True, help_text="Last push error")
    last_pushed_to_shopify = models.DateTimeField(null=True, blank=True)
    last_synced_from_shopify = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes")
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer Subscription'
        verbose_name_plural = 'Customer Subscriptions'
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['next_billing_date']),
            models.Index(fields=['needs_shopify_push']),
        ]
    
    def __str__(self):
        customer_name = f"{self.customer.first_name} {self.customer.last_name}" if self.customer else "Unknown"
        return f"Subscription for {customer_name} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Auto-track changes for bidirectional sync"""
        if not self.pk and not self.shopify_id:
            self.created_in_django = True
            self.needs_shopify_push = True
        elif self.pk and self.shopify_id:
            try:
                old = CustomerSubscription.objects.get(pk=self.pk)
                if (old.status != self.status or old.next_billing_date != self.next_billing_date or
                    old.line_items != self.line_items or old.delivery_address != self.delivery_address):
                    self.needs_shopify_push = True
            except CustomerSubscription.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def get_cutoff_date(self):
        """Calculate cutoff date based on next delivery date and product configurations"""
        if not self.next_delivery_date or not self.line_items:
            return None
            
        from datetime import timedelta
        from products.models import ShopifyProduct
        
        min_cutoff_days = 7  # Default cutoff
        
        # Find the longest cutoff period among all products in subscription
        for item in self.line_items:
            try:
                product = ShopifyProduct.objects.get(shopify_id=item.get('product_id'))
                if hasattr(product, 'shipping_config'):
                    min_cutoff_days = max(min_cutoff_days, product.shipping_config.cutoff_days)
            except ShopifyProduct.DoesNotExist:
                continue
        
        return self.next_delivery_date - timedelta(days=min_cutoff_days)
    
    def get_address(self):
        """Get effective delivery address (override or primary subscription address)"""
        # First check if there's a delivery address in the subscription
        if self.delivery_address:
            return self.delivery_address
        
        # Fall back to customer's primary subscription address
        if hasattr(self.customer, 'subscription_address'):
            addr = self.customer.subscription_address
            return {
                'first_name': addr.first_name,
                'last_name': addr.last_name,
                'company': addr.company,
                'address1': addr.address1,
                'address2': addr.address2,
                'city': addr.city,
                'province': addr.province,
                'country': addr.country,
                'zip': addr.zip_code,
                'phone': addr.phone,
            }
        
        return {}
    
    def get_line_items_display(self):
        """Return formatted line items"""
        if isinstance(self.line_items, str):
            try:
                return json.loads(self.line_items)
            except json.JSONDecodeError:
                return []
        return self.line_items or []


class SubscriptionBillingAttempt(models.Model):
    """
    Tracks subscription billing attempts
    """
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    subscription = models.ForeignKey(CustomerSubscription, on_delete=models.CASCADE, related_name='billing_attempts')
    shopify_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Billing Info
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Order Reference
    shopify_order_id = models.CharField(max_length=255, blank=True, help_text="Created order GID if successful")
    
    # Error Info
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    
    # Timing
    attempted_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-attempted_at']
        verbose_name = 'Billing Attempt'
        verbose_name_plural = 'Billing Attempts'
    
    def __str__(self):
        return f"{self.subscription} - {self.status} - ${self.amount}"


class SubscriptionSyncLog(models.Model):
    """
    Logs subscription sync operations (Django ↔ Shopify)
    """
    
    OPERATION_CHOICES = [
        ('import_from_shopify', 'Import from Shopify'),
        ('push_to_shopify', 'Push to Shopify'),
        ('update_in_shopify', 'Update in Shopify'),
        ('cancel_in_shopify', 'Cancel in Shopify'),
        ('bulk_sync', 'Bulk Sync'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    operation_type = models.CharField(max_length=50, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Statistics
    subscriptions_processed = models.IntegerField(default=0)
    subscriptions_successful = models.IntegerField(default=0)
    subscriptions_failed = models.IntegerField(default=0)
    
    # Error tracking
    error_details = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Subscription Sync Log'
        verbose_name_plural = 'Subscription Sync Logs'
    
    def __str__(self):
        return f"{self.operation_type} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
