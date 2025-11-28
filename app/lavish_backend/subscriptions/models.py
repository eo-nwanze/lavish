"""
Shopify Webhook Subscription Models

Manages webhook subscriptions for real-time event notifications from Shopify.
"""

from django.db import models
from django.utils import timezone


class ShopifyWebhookSubscription(models.Model):
    """
    Webhook subscriptions for receiving Shopify events
    """
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('xml', 'XML'),
    ]
    
    ENDPOINT_TYPE_CHOICES = [
        ('http', 'HTTP/HTTPS'),
        ('eventbridge', 'Amazon EventBridge'),
        ('pubsub', 'Google Cloud Pub/Sub'),
    ]
    
    # Common webhook topics
    TOPIC_CHOICES = [
        # Orders
        ('orders/create', 'Orders Create'),
        ('orders/updated', 'Orders Updated'),
        ('orders/cancelled', 'Orders Cancelled'),
        ('orders/fulfilled', 'Orders Fulfilled'),
        ('orders/paid', 'Orders Paid'),
        ('orders/partially_fulfilled', 'Orders Partially Fulfilled'),
        ('orders/delete', 'Orders Delete'),
        
        # Products
        ('products/create', 'Products Create'),
        ('products/update', 'Products Update'),
        ('products/delete', 'Products Delete'),
        
        # Customers
        ('customers/create', 'Customers Create'),
        ('customers/update', 'Customers Update'),
        ('customers/delete', 'Customers Delete'),
        ('customers/enable', 'Customers Enable'),
        ('customers/disable', 'Customers Disable'),
        
        # Inventory
        ('inventory_items/create', 'Inventory Items Create'),
        ('inventory_items/update', 'Inventory Items Update'),
        ('inventory_items/delete', 'Inventory Items Delete'),
        ('inventory_levels/connect', 'Inventory Levels Connect'),
        ('inventory_levels/update', 'Inventory Levels Update'),
        ('inventory_levels/disconnect', 'Inventory Levels Disconnect'),
        
        # Fulfillments
        ('fulfillments/create', 'Fulfillments Create'),
        ('fulfillments/update', 'Fulfillments Update'),
        
        # Refunds
        ('refunds/create', 'Refunds Create'),
        
        # Collections
        ('collections/create', 'Collections Create'),
        ('collections/update', 'Collections Update'),
        ('collections/delete', 'Collections Delete'),
        
        # App
        ('app/uninstalled', 'App Uninstalled'),
        
        # Shop
        ('shop/update', 'Shop Update'),
        
        # Checkouts
        ('checkouts/create', 'Checkouts Create'),
        ('checkouts/update', 'Checkouts Update'),
        ('checkouts/delete', 'Checkouts Delete'),
        
        # Disputes
        ('disputes/create', 'Disputes Create'),
        ('disputes/update', 'Disputes Update'),
        
        # Other
        ('other', 'Other'),
    ]
    
    # Basic Info
    shopify_id = models.CharField(max_length=255, unique=True)
    legacy_resource_id = models.BigIntegerField(null=True, blank=True)
    
    # Subscription Details
    topic = models.CharField(max_length=100, choices=TOPIC_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='json')
    
    # Endpoint Configuration
    endpoint_type = models.CharField(max_length=20, choices=ENDPOINT_TYPE_CHOICES, default='http')
    uri = models.URLField(max_length=500, help_text="Webhook destination URL")
    
    # API Version
    api_version = models.CharField(max_length=20, blank=True, default='', help_text="Admin API version")
    
    # Filtering
    filter_query = models.TextField(blank=True, default='', help_text="Search syntax filter for webhook events")
    include_fields = models.JSONField(default=list, blank=True, help_text="List of fields to include in payload")
    metafield_namespaces = models.JSONField(default=list, blank=True, help_text="Metafield namespaces to include")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Webhook Subscription'
        verbose_name_plural = 'Webhook Subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['topic', 'is_active']),
            models.Index(fields=['endpoint_type']),
        ]
    
    def __str__(self):
        return f"{self.topic} → {self.uri[:50]}"


class ShopifyWebhookDelivery(models.Model):
    """
    Tracks webhook delivery attempts and responses
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    subscription = models.ForeignKey(
        ShopifyWebhookSubscription,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    
    # Delivery Details
    delivery_id = models.CharField(max_length=255, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Request/Response
    request_payload = models.JSONField(blank=True, null=True)
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Timing
    attempted_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Webhook Delivery'
        verbose_name_plural = 'Webhook Deliveries'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['status', 'attempted_at']),
            models.Index(fields=['subscription', 'status']),
        ]
    
    def __str__(self):
        return f"{self.subscription.topic} - {self.status} ({self.attempted_at.strftime('%Y-%m-%d %H:%M')})"


class ShopifyWebhookSyncLog(models.Model):
    """
    Logs webhook subscription sync operations
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    OPERATION_CHOICES = [
        ('sync_all', 'Sync All Subscriptions'),
        ('create', 'Create Subscription'),
        ('update', 'Update Subscription'),
        ('delete', 'Delete Subscription'),
    ]
    
    operation_type = models.CharField(max_length=50, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Statistics
    subscriptions_synced = models.IntegerField(default=0)
    subscriptions_created = models.IntegerField(default=0)
    subscriptions_updated = models.IntegerField(default=0)
    subscriptions_deleted = models.IntegerField(default=0)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        verbose_name = 'Webhook Sync Log'
        verbose_name_plural = 'Webhook Sync Logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.operation_type} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
