from django.db import models
import json


class ShopifyOrder(models.Model):
    FINANCIAL_STATUS_CHOICES = [
        ('AUTHORIZED', 'Authorized'),
        ('PAID', 'Paid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
        ('PENDING', 'Pending'),
        ('REFUNDED', 'Refunded'),
        ('VOIDED', 'Voided'),
    ]
    
    FULFILLMENT_STATUS_CHOICES = [
        ('FULFILLED', 'Fulfilled'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('OPEN', 'Open'),
        ('PARTIALLY_FULFILLED', 'Partially Fulfilled'),
        ('PENDING_FULFILLMENT', 'Pending Fulfillment'),
        ('RESTOCKED', 'Restocked'),
        ('SCHEDULED', 'Scheduled'),
        ('UNFULFILLED', 'Unfulfilled'),
    ]
    """Model representing a Shopify order"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Global ID")
    order_number = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=50, help_text="Order name like #1001")
    
    # Customer information
    customer = models.ForeignKey('customers.ShopifyCustomer', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Order status
    financial_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('partially_refunded', 'Partially Refunded'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
    ])
    fulfillment_status = models.CharField(max_length=20, choices=[
        ('fulfilled', 'Fulfilled'),
        ('null', 'Unfulfilled'),
        ('partial', 'Partially Fulfilled'),
        ('restocked', 'Restocked'),
    ], null=True, blank=True)
    
    # Pricing
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_shipping_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency_code = models.CharField(max_length=10, default='AUD')
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    # Sync tracking
    last_synced = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(max_length=20, default='synced', choices=[
        ('synced', 'Synced'),
        ('pending', 'Pending Sync'),
        ('error', 'Sync Error'),
    ])
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['shopify_id']),
            models.Index(fields=['financial_status']),
            models.Index(fields=['fulfillment_status']),
            models.Index(fields=['customer']),
        ]
    
    def __str__(self):
        return f"Order {self.name} - {self.customer_email}"


class ShopifyOrderLineItem(models.Model):
    """Model representing a Shopify order line item"""
    
    order = models.ForeignKey(ShopifyOrder, on_delete=models.CASCADE, related_name='line_items')
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Line Item ID")
    
    # Product information
    product = models.ForeignKey('products.ShopifyProduct', on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey('products.ShopifyProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Item details
    title = models.CharField(max_length=255)
    variant_title = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100, blank=True)
    
    # Quantity and pricing
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Properties
    properties = models.JSONField(default=list, blank=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['order']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return f"{self.order.name} - {self.title} (x{self.quantity})"


class ShopifyOrderAddress(models.Model):
    """Model representing order shipping/billing addresses"""
    
    order = models.ForeignKey(ShopifyOrder, on_delete=models.CASCADE, related_name='addresses')
    
    # Address type
    address_type = models.CharField(max_length=20, choices=[
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    ])
    
    # Address fields
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Geographic codes
    province_code = models.CharField(max_length=10, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['order', 'address_type']
        unique_together = ['order', 'address_type']
    
    def __str__(self):
        return f"{self.order.name} - {self.address_type} address"


class OrderSyncLog(models.Model):
    """Log of order synchronization operations"""
    
    operation_type = models.CharField(max_length=20, choices=[
        ('bulk_import', 'Bulk Import'),
        ('single_update', 'Single Update'),
        ('webhook_update', 'Webhook Update'),
    ])
    
    orders_processed = models.IntegerField(default=0)
    orders_created = models.IntegerField(default=0)
    orders_updated = models.IntegerField(default=0)
    line_items_processed = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, default='running', choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    
    error_details = models.JSONField(null=True, blank=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.operation_type} - {self.status} ({self.started_at})"
