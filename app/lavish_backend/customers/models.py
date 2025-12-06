from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class ShopifyCustomer(models.Model):
    """Model representing a Shopify customer"""
    
    # Shopify fields
    shopify_id = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Shopify Global ID")
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    
    # Bidirectional sync fields
    needs_shopify_push = models.BooleanField(default=False, help_text="True if customer needs to be pushed to Shopify")
    shopify_push_error = models.TextField(blank=True, help_text="Last error message from Shopify push")
    last_pushed_to_shopify = models.DateTimeField(null=True, blank=True, help_text="Last successful push to Shopify")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['shopify_id']),
            models.Index(fields=['state']),
            models.Index(fields=['store_domain']),
            models.Index(fields=['needs_shopify_push']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def save(self, *args, **kwargs):
        """Override save to detect changes and flag for Shopify push"""
        import time
        
        # If this is a new customer without shopify_id, generate temp ID
        if not self.pk and not self.shopify_id:
            timestamp = int(time.time())
            self.shopify_id = f"temp_customer_{timestamp}"
            self.needs_shopify_push = True
        
        if self.pk:  # Only for existing records
            try:
                old_instance = ShopifyCustomer.objects.get(pk=self.pk)
                # Check if any synced fields changed
                if (old_instance.email != self.email or
                    old_instance.first_name != self.first_name or
                    old_instance.last_name != self.last_name or
                    old_instance.phone != self.phone or
                    old_instance.tags != self.tags or
                    old_instance.accepts_marketing != self.accepts_marketing):
                    self.needs_shopify_push = True
            except ShopifyCustomer.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
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
    shopify_id = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Shopify Address ID")
    
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
    
    # Bidirectional Sync Tracking
    needs_shopify_push = models.BooleanField(default=False, help_text="True if needs push to Shopify")
    shopify_push_error = models.TextField(blank=True, help_text="Last push error message")
    last_pushed_to_shopify = models.DateTimeField(null=True, blank=True, help_text="When last pushed to Shopify")
    
    class Meta:
        ordering = ['-is_default', 'id']
        indexes = [
            models.Index(fields=['customer', 'is_default']),
            models.Index(fields=['country_code']),
            models.Index(fields=['province_code']),
            models.Index(fields=['needs_shopify_push']),
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
    
    def save(self, *args, **kwargs):
        """Auto-track changes for bidirectional sync"""
        # Skip auto-push during sync operations
        skip_push_flag = kwargs.pop('skip_push_flag', False)
        
        if self.pk and not skip_push_flag:
            # Check if address changed
            try:
                old = ShopifyCustomerAddress.objects.get(pk=self.pk)
                # Check if any address field changed
                if (old.address1 != self.address1 or old.address2 != self.address2 or
                    old.city != self.city or old.province != self.province or
                    old.country != self.country or old.zip_code != self.zip_code or
                    old.phone != self.phone or old.is_default != self.is_default or
                    old.first_name != self.first_name or old.last_name != self.last_name or
                    old.company != self.company):
                    self.needs_shopify_push = True
            except ShopifyCustomerAddress.DoesNotExist:
                pass
        elif not self.pk:
            # New record - if created in Django, mark for push
            self.needs_shopify_push = True
            # Generate temporary ID if not set
            if not self.shopify_id:
                self.shopify_id = f"temp_address_{timezone.now().timestamp()}"
                
        super().save(*args, **kwargs)


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
