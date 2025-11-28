from django.db import models


class ShopifyCarrierService(models.Model):
    """Model representing a Shopify carrier service"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Carrier Service ID")
    name = models.CharField(max_length=255)
    
    # Service configuration
    active = models.BooleanField(default=True)
    service_discovery = models.BooleanField(default=False)
    carrier_service_type = models.CharField(max_length=20, choices=[
        ('api', 'API'),
        ('legacy', 'Legacy'),
    ])
    
    # API configuration
    callback_url = models.URLField(blank=True, help_text="Callback URL for rate calculations")
    format = models.CharField(max_length=10, default='json', choices=[
        ('json', 'JSON'),
        ('xml', 'XML'),
    ])
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['active']),
        ]
    
    def __str__(self):
        return self.name


class ShopifyDeliveryProfile(models.Model):
    """Model representing a Shopify delivery profile"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Delivery Profile ID")
    name = models.CharField(max_length=255)
    
    # Profile settings
    active = models.BooleanField(default=True)
    default = models.BooleanField(default=False)
    
    # Location associations
    locations_without_rates_to_ship = models.JSONField(default=list, blank=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['active']),
            models.Index(fields=['default']),
        ]
    
    def __str__(self):
        return self.name


class ShopifyDeliveryZone(models.Model):
    """Model representing a Shopify delivery zone"""
    
    # Relationships
    profile = models.ForeignKey(ShopifyDeliveryProfile, on_delete=models.CASCADE, related_name='zones')
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Delivery Zone ID")
    name = models.CharField(max_length=255)
    
    # Geographic coverage
    countries = models.JSONField(default=list, help_text="List of country codes")
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['profile', 'name']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['profile']),
        ]
    
    def __str__(self):
        return f"{self.profile.name} - {self.name}"


class ShopifyDeliveryMethod(models.Model):
    """Model representing a Shopify delivery method"""
    
    # Relationships
    zone = models.ForeignKey(ShopifyDeliveryZone, on_delete=models.CASCADE, related_name='methods')
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Delivery Method ID")
    name = models.CharField(max_length=255)
    
    # Method configuration
    method_type = models.CharField(max_length=20, choices=[
        ('shipping', 'Shipping'),
        ('pickup', 'Pickup'),
    ])
    
    # Pricing
    min_delivery_date_time = models.DateTimeField(null=True, blank=True)
    max_delivery_date_time = models.DateTimeField(null=True, blank=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['zone', 'name']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['zone']),
            models.Index(fields=['method_type']),
        ]
    
    def __str__(self):
        return f"{self.zone.name} - {self.name}"


class ShopifyFulfillmentOrder(models.Model):
    """Model representing a Shopify fulfillment order"""
    
    # Relationships
    order = models.ForeignKey('orders.ShopifyOrder', on_delete=models.CASCADE, related_name='fulfillment_orders')
    location = models.ForeignKey('inventory.ShopifyLocation', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Fulfillment Order ID")
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('cancelled', 'Cancelled'),
        ('incomplete', 'Incomplete'),
        ('closed', 'Closed'),
    ])
    
    request_status = models.CharField(max_length=30, choices=[
        ('unsubmitted', 'Unsubmitted'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancellation_requested', 'Cancellation Requested'),
        ('cancellation_accepted', 'Cancellation Accepted'),
        ('closed', 'Closed'),
    ])
    
    # Fulfillment details
    fulfill_at = models.DateTimeField(null=True, blank=True)
    fulfill_by = models.DateTimeField(null=True, blank=True)
    
    # International duties
    international_duties = models.JSONField(null=True, blank=True)
    
    # Delivery information
    delivery_method = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"Fulfillment Order {self.shopify_id} - {self.status}"


class ShopifyFulfillmentService(models.Model):
    """Model representing a Shopify fulfillment service"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Fulfillment Service ID")
    name = models.CharField(max_length=255)
    handle = models.CharField(max_length=255)
    
    # Service configuration
    email = models.EmailField(blank=True)
    service_name = models.CharField(max_length=255, blank=True)
    
    # Capabilities
    include_pending_stock = models.BooleanField(default=False)
    requires_shipping_method = models.BooleanField(default=False)
    tracking_support = models.BooleanField(default=False)
    
    # API configuration
    callback_url = models.URLField(blank=True)
    format = models.CharField(max_length=10, default='json', choices=[
        ('json', 'JSON'),
        ('xml', 'XML'),
    ])
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['handle']),
        ]
    
    def __str__(self):
        return self.name


class ShippingSyncLog(models.Model):
    """Log of shipping synchronization operations"""
    
    operation_type = models.CharField(max_length=20, choices=[
        ('bulk_import', 'Bulk Import'),
        ('single_update', 'Single Update'),
        ('webhook_update', 'Webhook Update'),
    ])
    
    carriers_processed = models.IntegerField(default=0)
    profiles_processed = models.IntegerField(default=0)
    zones_processed = models.IntegerField(default=0)
    methods_processed = models.IntegerField(default=0)
    fulfillment_orders_processed = models.IntegerField(default=0)
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
