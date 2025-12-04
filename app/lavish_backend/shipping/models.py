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


class ShippingRate(models.Model):
    """Model storing live shipping rates from Shopify carriers"""
    
    # Relationships
    carrier = models.ForeignKey(
        ShopifyCarrierService, 
        on_delete=models.CASCADE, 
        related_name='rates',
        null=True,
        blank=True
    )
    delivery_method = models.ForeignKey(
        ShopifyDeliveryMethod,
        on_delete=models.CASCADE,
        related_name='rates',
        null=True,
        blank=True
    )
    
    # Rate identification (following Shopify ShippingRate object)
    handle = models.CharField(max_length=255, help_text="Unique identifier for this rate")
    title = models.CharField(max_length=255, help_text="Display name of the shipping rate")
    
    # Pricing (MoneyV2 structure)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rate price amount")
    price_currency = models.CharField(max_length=3, default='USD', help_text="Currency code (USD, CAD, etc.)")
    
    # Additional details
    description = models.TextField(blank=True, help_text="Service description")
    
    # Service level
    service_code = models.CharField(max_length=100, blank=True, help_text="Service code (STANDARD, EXPRESS, etc.)")
    
    # Delivery estimates
    min_delivery_days = models.IntegerField(null=True, blank=True, help_text="Minimum delivery days")
    max_delivery_days = models.IntegerField(null=True, blank=True, help_text="Maximum delivery days")
    
    # Geographic scope
    origin_country = models.CharField(max_length=2, blank=True, help_text="Origin country code")
    destination_country = models.CharField(max_length=2, blank=True, help_text="Destination country code")
    destination_zone = models.CharField(max_length=255, blank=True, help_text="Destination zone name")
    
    # Metadata
    phone_required = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    
    # Sync tracking
    last_synced = models.DateTimeField(auto_now=True)
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    # Sample request used to generate this rate
    sample_weight_grams = models.IntegerField(null=True, blank=True, help_text="Sample package weight")
    sample_value_cents = models.IntegerField(null=True, blank=True, help_text="Sample package value")
    
    class Meta:
        ordering = ['destination_country', 'price_amount']
        indexes = [
            models.Index(fields=['carrier']),
            models.Index(fields=['delivery_method']),
            models.Index(fields=['destination_country']),
            models.Index(fields=['active']),
            models.Index(fields=['handle']),
        ]
        verbose_name = 'Shipping Rate'
        verbose_name_plural = 'Shipping Rates'
    
    def __str__(self):
        # Show carrier if available, otherwise show delivery method zone/profile
        if self.carrier:
            carrier_name = self.carrier.name
        elif self.delivery_method:
            carrier_name = f"{self.delivery_method.zone.profile.name}"
        else:
            carrier_name = 'Unknown'
        return f"{carrier_name} - {self.title} ({self.destination_country}): {self.price_amount} {self.price_currency}"


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


class FulfillmentTrackingInfo(models.Model):
    """
    Model representing Shopify fulfillment tracking information.
    
    Tracks shipment information for fulfillments including carrier, tracking number,
    and tracking URL. Supports all major shipping carriers recognized by Shopify.
    
    Shopify API Reference: FulfillmentTrackingInfo object
    Requires: read_orders, read_marketplace_orders, read_assigned_fulfillment_orders,
              read_merchant_managed_fulfillment_orders, read_third_party_fulfillment_orders,
              or read_marketplace_fulfillment_orders access scope.
    """
    
    # Relationship to fulfillment order
    fulfillment_order = models.ForeignKey(
        ShopifyFulfillmentOrder,
        on_delete=models.CASCADE,
        related_name='tracking_info',
        help_text="The fulfillment order this tracking info belongs to"
    )
    
    # Core tracking fields (from Shopify FulfillmentTrackingInfo object)
    company = models.CharField(
        max_length=255,
        blank=True,
        help_text="The name of the tracking company (e.g., FedEx, UPS, USPS, DHL)"
    )
    
    number = models.CharField(
        max_length=255,
        blank=True,
        help_text="The tracking number provided by the shipping carrier"
    )
    
    url = models.URLField(
        max_length=500,
        blank=True,
        help_text="The URL to track the fulfillment on the carrier's website"
    )
    
    # Additional metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this tracking info is currently active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Store reference
    store_domain = models.CharField(max_length=100, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['fulfillment_order']),
            models.Index(fields=['company']),
            models.Index(fields=['number']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Fulfillment Tracking Info'
        verbose_name_plural = 'Fulfillment Tracking Info'
    
    def __str__(self):
        if self.company and self.number:
            return f"{self.company}: {self.number}"
        elif self.number:
            return f"Tracking: {self.number}"
        elif self.company:
            return f"{self.company} (no tracking number)"
        return f"Tracking Info #{self.id}"
    
    def get_tracking_url(self):
        """
        Get the tracking URL, preferring the explicit URL field.
        Falls back to auto-generated URL based on carrier if available.
        """
        if self.url:
            return self.url
        
        # Auto-generate tracking URLs for known carriers
        if self.company and self.number:
            carrier_urls = {
                'FedEx': f'https://www.fedex.com/fedextrack/?trknbr={self.number}',
                'UPS': f'https://www.ups.com/track?tracknum={self.number}',
                'USPS': f'https://tools.usps.com/go/TrackConfirmAction?tLabels={self.number}',
                'DHL': f'https://www.dhl.com/en/express/tracking.html?AWB={self.number}',
                'DHL Express': f'https://www.dhl.com/en/express/tracking.html?AWB={self.number}',
                'Canada Post': f'https://www.canadapost-postescanada.ca/track-reperage/en#/search?searchFor={self.number}',
                'Australia Post': f'https://auspost.com.au/mypost/track/#/details/{self.number}',
                'Royal Mail': f'https://www.royalmail.com/track-your-item#/tracking-results/{self.number}',
                'Purolator': f'https://www.purolator.com/en/ship-track/tracking-details.page?pin={self.number}',
                'Sendle': f'https://track.sendle.com/{self.number}',
            }
            
            for carrier_name, url_template in carrier_urls.items():
                if carrier_name.lower() in self.company.lower():
                    return url_template
        
        return None
    
    @property
    def tracking_url_display(self):
        """Get tracking URL for display in admin"""
        return self.get_tracking_url() or "No tracking URL available"
