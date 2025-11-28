from django.db import models


class ShopifyStore(models.Model):
    """Model representing a Shopify store configuration"""
    
    # Store identification
    store_domain = models.CharField(max_length=100, unique=True, help_text="e.g., 7fa66c-ac.myshopify.com")
    store_name = models.CharField(max_length=100, help_text="Business name")
    
    # API credentials
    api_key = models.CharField(max_length=100)
    api_secret = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)
    api_version = models.CharField(max_length=20, default='2025-01')
    
    # Store details
    currency = models.CharField(max_length=10, default='AUD')
    timezone = models.CharField(max_length=50, default='Australia/Sydney')
    country_code = models.CharField(max_length=10, default='AU')
    
    # Status
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['store_name']
    
    def __str__(self):
        return f"{self.store_name} ({self.store_domain})"


class WebhookEndpoint(models.Model):
    """Model for managing Shopify webhooks"""
    
    store = models.ForeignKey(ShopifyStore, on_delete=models.CASCADE, related_name='webhooks')
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Webhook ID")
    
    # Webhook configuration
    topic = models.CharField(max_length=100, help_text="e.g., orders/create, customers/update")
    address = models.URLField(help_text="Webhook endpoint URL")
    format = models.CharField(max_length=20, default='json', choices=[
        ('json', 'JSON'),
        ('xml', 'XML'),
    ])
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['topic']
        unique_together = ['store', 'topic']
    
    def __str__(self):
        return f"{self.store.store_name} - {self.topic}"


class SyncOperation(models.Model):
    """Model for tracking synchronization operations"""
    
    store = models.ForeignKey(ShopifyStore, on_delete=models.CASCADE, related_name='sync_operations')
    
    # Operation details
    operation_type = models.CharField(max_length=50, choices=[
        ('customers_sync', 'Customers Sync'),
        ('products_sync', 'Products Sync'),
        ('orders_sync', 'Orders Sync'),
        ('inventory_sync', 'Inventory Sync'),
        ('shipping_sync', 'Shipping Sync'),
        ('full_sync', 'Full Sync'),
    ])
    
    # Status tracking
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ])
    
    # Progress tracking
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    created_records = models.IntegerField(default=0)
    updated_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.store.store_name} - {self.operation_type} ({self.status})"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_records == 0:
            return 0
        return (self.processed_records / self.total_records) * 100


class APIRateLimit(models.Model):
    """Model for tracking Shopify API rate limits"""
    
    store = models.ForeignKey(ShopifyStore, on_delete=models.CASCADE, related_name='rate_limits')
    
    # Rate limit details
    api_type = models.CharField(max_length=20, choices=[
        ('rest', 'REST API'),
        ('graphql', 'GraphQL API'),
    ])
    
    # Current limits
    current_calls = models.IntegerField(default=0)
    max_calls = models.IntegerField(default=40)  # Shopify default
    
    # Timing
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    
    # Status
    is_throttled = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['store', 'api_type']
    
    def __str__(self):
        return f"{self.store.store_name} - {self.api_type} ({self.current_calls}/{self.max_calls})"
    
    @property
    def usage_percentage(self):
        """Calculate API usage percentage"""
        if self.max_calls == 0:
            return 0
        return (self.current_calls / self.max_calls) * 100
