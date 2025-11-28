from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class ShopifyCustomer(models.Model):
    """Model representing a Shopify customer"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Global ID")
    email = models.EmailField(max_length=254, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Status and verification
    state = models.CharField(max_length=20, default='ENABLED', choices=[
        ('ENABLED', 'Enabled'),
        ('DISABLED', 'Disabled'),
    ])
    verified_email = models.BooleanField(default=False)
    tax_exempt = models.BooleanField(default=False)
    
    # Order information
    number_of_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Marketing and tags
    tags = models.JSONField(default=list, blank=True, help_text="Customer tags as JSON array")
    accepts_marketing = models.BooleanField(default=False)
    marketing_opt_in_level = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    # Local user association (optional)
    local_user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    
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
            models.Index(fields=['email']),
            models.Index(fields=['shopify_id']),
            models.Index(fields=['state']),
            models.Index(fields=['store_domain']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_tags_list(self):
        """Return tags as a Python list"""
        if isinstance(self.tags, str):
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return self.tags or []


class ShopifyCustomerAddress(models.Model):
    """Model representing a Shopify customer address"""
    
    customer = models.ForeignKey(ShopifyCustomer, on_delete=models.CASCADE, related_name='addresses')
    shopify_id = models.CharField(max_length=100, unique=True, help_text="Shopify Address ID")
    
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
    country_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['-is_default', 'id']
        indexes = [
            models.Index(fields=['customer', 'is_default']),
            models.Index(fields=['country_code']),
            models.Index(fields=['province_code']),
        ]
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.city}, {self.province}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [
            self.address1,
            self.address2,
            self.city,
            self.province,
            self.country,
            self.zip_code
        ]
        return ', '.join([part for part in parts if part])


class CustomerSyncLog(models.Model):
    """Log of customer synchronization operations"""
    
    operation_type = models.CharField(max_length=20, choices=[
        ('bulk_import', 'Bulk Import'),
        ('single_update', 'Single Update'),
        ('webhook_update', 'Webhook Update'),
    ])
    
    customers_processed = models.IntegerField(default=0)
    customers_created = models.IntegerField(default=0)
    customers_updated = models.IntegerField(default=0)
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
