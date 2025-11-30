from django.db import models
import json


class ShopifyProduct(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
        ('DRAFT', 'Draft'),
    ]
    """Model representing a Shopify product"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Global ID")
    title = models.CharField(max_length=255)
    handle = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Product details
    product_type = models.CharField(max_length=100, blank=True)
    vendor = models.CharField(max_length=100, blank=True)
    
    # Status and visibility
    status = models.CharField(max_length=20, default='DRAFT', choices=[
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
        ('DRAFT', 'Draft'),
    ])
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO and metadata
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True, help_text="Product tags as JSON array")
    
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
    
    # Bidirectional sync tracking
    created_in_django = models.BooleanField(default=False, help_text="True if product was created in Django (not imported from Shopify)")
    needs_shopify_push = models.BooleanField(default=False, help_text="True if product needs to be pushed to Shopify")
    shopify_push_error = models.TextField(blank=True, help_text="Error message if push to Shopify failed")
    last_pushed_to_shopify = models.DateTimeField(null=True, blank=True, help_text="Last time product was pushed to Shopify")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['handle']),
            models.Index(fields=['shopify_id']),
            models.Index(fields=['status']),
            models.Index(fields=['product_type']),
            models.Index(fields=['vendor']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Override save to handle bidirectional sync tracking"""
        # If this is a new product without shopify_id, it was created in Django
        if not self.pk and not self.shopify_id:
            self.created_in_django = True
            self.needs_shopify_push = True
        
        # If product has been modified and has a shopify_id, mark for update
        if self.pk and self.shopify_id:
            try:
                old_product = ShopifyProduct.objects.get(pk=self.pk)
                # Check if important fields changed
                if (old_product.title != self.title or 
                    old_product.description != self.description or
                    old_product.vendor != self.vendor or
                    old_product.product_type != self.product_type or
                    old_product.status != self.status or
                    old_product.tags != self.tags):
                    self.needs_shopify_push = True
            except ShopifyProduct.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Return tags as a Python list"""
        if isinstance(self.tags, str):
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return self.tags or []


class ShopifyProductVariant(models.Model):
    """Model representing a Shopify product variant"""
    
    product = models.ForeignKey(ShopifyProduct, on_delete=models.CASCADE, related_name='variants')
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Variant ID")
    
    # Variant details
    title = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_per_item = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    inventory_quantity = models.IntegerField(default=0)
    inventory_policy = models.CharField(max_length=20, default='deny', choices=[
        ('deny', 'Deny'),
        ('continue', 'Continue'),
    ])
    inventory_management = models.CharField(max_length=50, blank=True)
    
    # Physical properties
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    weight_unit = models.CharField(max_length=10, default='kg')
    
    # Variant options
    option1 = models.CharField(max_length=255, blank=True)
    option2 = models.CharField(max_length=255, blank=True)
    option3 = models.CharField(max_length=255, blank=True)
    
    # Status
    available = models.BooleanField(default=True)
    requires_shipping = models.BooleanField(default=True)
    taxable = models.BooleanField(default=True)
    
    # Position
    position = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['product', 'position']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['shopify_id']),
            models.Index(fields=['product', 'position']),
        ]
    
    def __str__(self):
        return f"{self.product.title} - {self.title}"


class ShopifyProductImage(models.Model):
    """Model representing a Shopify product image"""
    
    product = models.ForeignKey(ShopifyProduct, on_delete=models.CASCADE, related_name='images')
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Image ID")
    
    # Image details
    src = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=255, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    # Position
    position = models.IntegerField(default=1)
    
    # Variant associations
    variant_ids = models.JSONField(default=list, blank=True, help_text="Associated variant IDs as JSON array")
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['product', 'position']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['product', 'position']),
        ]
    
    def __str__(self):
        return f"{self.product.title} - Image {self.position}"
    
    def get_variant_ids_list(self):
        """Return variant IDs as a Python list"""
        if isinstance(self.variant_ids, str):
            try:
                return json.loads(self.variant_ids)
            except json.JSONDecodeError:
                return []
        return self.variant_ids or []


class ShopifyProductMetafield(models.Model):
    """Model representing Shopify product metafields"""
    
    product = models.ForeignKey(ShopifyProduct, on_delete=models.CASCADE, related_name='metafields')
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Metafield ID")
    
    # Metafield details
    namespace = models.CharField(max_length=100)
    key = models.CharField(max_length=100)
    value = models.TextField()
    value_type = models.CharField(max_length=50, default='string')
    description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['product', 'namespace', 'key']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['product', 'namespace']),
            models.Index(fields=['namespace', 'key']),
        ]
        unique_together = ['product', 'namespace', 'key']
    
    def __str__(self):
        return f"{self.product.title} - {self.namespace}.{self.key}"


class ProductSyncLog(models.Model):
    """Log of product synchronization operations"""
    
    operation_type = models.CharField(max_length=20, choices=[
        ('bulk_import', 'Bulk Import'),
        ('single_update', 'Single Update'),
        ('webhook_update', 'Webhook Update'),
    ])
    
    products_processed = models.IntegerField(default=0)
    products_created = models.IntegerField(default=0)
    products_updated = models.IntegerField(default=0)
    variants_processed = models.IntegerField(default=0)
    images_processed = models.IntegerField(default=0)
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
