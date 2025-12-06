from django.db import models
from django.utils import timezone


class ShopifyLocation(models.Model):
    """Model representing a Shopify location/warehouse"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Location ID")
    name = models.CharField(max_length=255)
    
    # Address information
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Location settings
    active = models.BooleanField(default=True)
    legacy = models.BooleanField(default=False)
    
    # Capabilities
    fulfills_online_orders = models.BooleanField(default=True)
    fulfillment_service = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
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


class ShopifyInventoryItem(models.Model):
    """Model representing a Shopify inventory item"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Inventory Item ID")
    sku = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Inventory settings
    tracked = models.BooleanField(default=True)
    requires_shipping = models.BooleanField(default=True)
    
    # Cost information
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Product variant relationship
    variant = models.OneToOneField('products.ShopifyProductVariant', on_delete=models.CASCADE, related_name='inventory_item', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
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
        ordering = ['sku']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['sku']),
            models.Index(fields=['tracked']),
        ]
    
    def __str__(self):
        if self.variant:
            return f"{self.sku} - {self.variant.title} ({self.variant.product.title})"
        return f"{self.sku} - Inventory Item"


class ShopifyInventoryLevel(models.Model):
    """Model representing inventory levels at specific locations"""
    
    # Relationships
    inventory_item = models.ForeignKey(ShopifyInventoryItem, on_delete=models.CASCADE, related_name='levels')
    location = models.ForeignKey(ShopifyLocation, on_delete=models.CASCADE, related_name='inventory_levels')
    
    # Inventory quantities
    available = models.IntegerField(default=0, help_text="Available quantity")
    committed = models.IntegerField(default=0, help_text="Committed quantity")
    incoming = models.IntegerField(default=0, help_text="Incoming quantity")
    on_hand = models.IntegerField(default=0, help_text="On hand quantity")
    
    # Timestamps
    updated_at = models.DateTimeField()
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    # Bidirectional Sync Tracking
    needs_shopify_push = models.BooleanField(default=False, help_text="True if needs push to Shopify")
    shopify_push_error = models.TextField(blank=True, help_text="Last push error message")
    last_pushed_to_shopify = models.DateTimeField(null=True, blank=True, help_text="When last pushed to Shopify")
    last_synced = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['inventory_item', 'location']
        unique_together = ['inventory_item', 'location']
        indexes = [
            models.Index(fields=['inventory_item', 'location']),
            models.Index(fields=['available']),
            models.Index(fields=['needs_shopify_push']),
        ]
    
    def __str__(self):
        if self.inventory_item.variant:
            product_name = f"{self.inventory_item.variant.product.title} - {self.inventory_item.variant.title}"
            return f"{product_name} at {self.location.name}: {self.available} available"
        return f"{self.inventory_item.sku} at {self.location.name}: {self.available} available"
    
    @property
    def total_quantity(self):
        """Calculate total quantity (available + committed)"""
        return self.available + self.committed
    
    def save(self, *args, **kwargs):
        """Auto-track changes for bidirectional sync"""
        # Skip auto-push during sync operations
        skip_push_flag = kwargs.pop('skip_push_flag', False)
        
        if self.pk and not skip_push_flag:
            # Check if quantity changed
            try:
                old = ShopifyInventoryLevel.objects.get(pk=self.pk)
                if old.available != self.available:
                    self.needs_shopify_push = True
                    self.updated_at = timezone.now()
            except ShopifyInventoryLevel.DoesNotExist:
                pass
        elif not self.pk:
            # New record - if created in Django, mark for push
            self.needs_shopify_push = True
            if not self.updated_at:
                self.updated_at = timezone.now()
                
        super().save(*args, **kwargs)


class InventoryAdjustment(models.Model):
    """Model for tracking inventory adjustments"""
    
    # Relationships
    inventory_item = models.ForeignKey(ShopifyInventoryItem, on_delete=models.CASCADE, related_name='adjustments')
    location = models.ForeignKey(ShopifyLocation, on_delete=models.CASCADE, related_name='adjustments')
    
    # Adjustment details
    adjustment_type = models.CharField(max_length=20, choices=[
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
        ('recount', 'Recount'),
        ('correction', 'Correction'),
    ])
    
    quantity_delta = models.IntegerField(help_text="Change in quantity (positive or negative)")
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Before and after quantities
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    
    # User tracking
    adjusted_by = models.CharField(max_length=100, blank=True, help_text="User who made the adjustment")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory_item', 'location']),
            models.Index(fields=['adjustment_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.inventory_item.sku} {self.adjustment_type}: {self.quantity_delta}"


class InventorySyncLog(models.Model):
    """Log of inventory synchronization operations"""
    
    operation_type = models.CharField(max_length=20, choices=[
        ('bulk_import', 'Bulk Import'),
        ('single_update', 'Single Update'),
        ('webhook_update', 'Webhook Update'),
        ('adjustment', 'Adjustment'),
    ])
    
    items_processed = models.IntegerField(default=0)
    items_created = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    levels_processed = models.IntegerField(default=0)
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
