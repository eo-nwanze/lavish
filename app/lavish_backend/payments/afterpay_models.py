"""
Afterpay Payment Integration Models
Handles Afterpay credentials, checkouts, and payment tracking
"""

from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator
import uuid


class AfterpayConfiguration(models.Model):
    """
    Afterpay API Configuration
    Stores merchant credentials and settings for Afterpay integration
    """
    
    ENVIRONMENT_CHOICES = [
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production (Live)'),
    ]
    
    REGION_CHOICES = [
        ('US', 'United States'),
        ('AU', 'Australia'),
        ('NZ', 'New Zealand'),
        ('CA', 'Canada'),
        ('GB', 'United Kingdom'),
    ]
    
    # Identification
    name = models.CharField(
        max_length=255,
        default="Afterpay Configuration",
        help_text="Configuration name for identification"
    )
    
    # Environment
    environment = models.CharField(
        max_length=20,
        choices=ENVIRONMENT_CHOICES,
        default='sandbox',
        help_text="API environment (sandbox for testing, production for live)"
    )
    
    region = models.CharField(
        max_length=2,
        choices=REGION_CHOICES,
        default='US',
        help_text="Merchant region"
    )
    
    # Credentials
    merchant_id = models.CharField(
        max_length=255,
        help_text="Afterpay Merchant ID (username for Basic Auth)"
    )
    
    secret_key = models.CharField(
        max_length=255,
        help_text="Afterpay Secret Key (password for Basic Auth)"
    )
    
    # Configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this configuration"
    )
    
    is_default = models.BooleanField(
        default=False,
        help_text="Set as default Afterpay configuration"
    )
    
    # Payment Limits (cached from API)
    min_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum payment amount (fetched from Afterpay API)"
    )
    
    max_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum payment amount (fetched from Afterpay API)"
    )
    
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Default currency code"
    )
    
    # Last configuration fetch
    config_last_fetched = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time configuration was fetched from Afterpay"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Afterpay Configuration'
        verbose_name_plural = 'Afterpay Configurations'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        env_label = "LIVE" if self.environment == 'production' else "TEST"
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.name} ({env_label} - {self.region})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default configuration
        if self.is_default:
            AfterpayConfiguration.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def api_base_url(self):
        """Get the appropriate API base URL"""
        if self.environment == 'production':
            return 'https://global-api.afterpay.com'
        return 'https://global-api-sandbox.afterpay.com'
    
    @property
    def portal_url(self):
        """Get the appropriate portal URL"""
        if self.environment == 'production':
            return 'https://portal.afterpay.com'
        return 'https://portal.sandbox.afterpay.com'


class AfterpayCheckout(models.Model):
    """
    Afterpay Checkout Session
    Tracks checkout sessions created with Afterpay
    """
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('captured', 'Captured'),
        ('auth_approved', 'Auth Approved'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Afterpay Data
    afterpay_token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Token returned from Afterpay checkout creation"
    )
    
    afterpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Afterpay Order ID (after auth/capture)"
    )
    
    # Configuration
    configuration = models.ForeignKey(
        AfterpayConfiguration,
        on_delete=models.PROTECT,
        related_name='checkouts',
        help_text="Afterpay configuration used for this checkout"
    )
    
    # Order Information
    merchant_reference = models.CharField(
        max_length=255,
        help_text="Merchant's order reference/ID"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total order amount"
    )
    
    currency = models.CharField(max_length=3, default='USD')
    
    # Customer Information
    customer_email = models.EmailField(help_text="Customer email address")
    customer_first_name = models.CharField(max_length=255, blank=True)
    customer_last_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        help_text="Current checkout/payment status"
    )
    
    payment_state = models.CharField(
        max_length=50,
        blank=True,
        help_text="Afterpay payment state"
    )
    
    # URLs
    redirect_checkout_url = models.URLField(
        max_length=500,
        help_text="URL to redirect customer for Afterpay checkout"
    )
    
    # Timestamps
    expires_at = models.DateTimeField(
        help_text="When the checkout token expires"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Shopify Integration
    shopify_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Associated Shopify order ID"
    )
    
    subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Associated subscription ID"
    )
    
    class Meta:
        verbose_name = 'Afterpay Checkout'
        verbose_name_plural = 'Afterpay Checkouts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['afterpay_token']),
            models.Index(fields=['merchant_reference']),
            models.Index(fields=['status']),
            models.Index(fields=['shopify_order_id']),
        ]
    
    def __str__(self):
        return f"Afterpay Checkout {self.merchant_reference} - {self.status} (${self.amount})"
    
    @property
    def is_expired(self):
        """Check if checkout has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_completed(self):
        """Check if payment is completed"""
        return self.status in ['captured', 'approved']


class AfterpayPaymentEvent(models.Model):
    """
    Afterpay Payment Event
    Tracks individual payment events (auth, capture, refund, etc.)
    """
    
    EVENT_TYPES = [
        ('AUTH_APPROVED', 'Authorization Approved'),
        ('CAPTURED', 'Payment Captured'),
        ('REFUNDED', 'Payment Refunded'),
        ('VOIDED', 'Payment Voided'),
        ('DECLINED', 'Payment Declined'),
        ('EXPIRED', 'Authorization Expired'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    afterpay_event_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Afterpay's event ID"
    )
    
    # Related Checkout
    checkout = models.ForeignKey(
        AfterpayCheckout,
        on_delete=models.CASCADE,
        related_name='events',
        help_text="Associated checkout session"
    )
    
    # Event Details
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        help_text="Type of payment event"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount for this event"
    )
    
    currency = models.CharField(max_length=3)
    
    merchant_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Merchant reference for this specific event"
    )
    
    # Timestamps
    event_created_at = models.DateTimeField(
        help_text="When Afterpay created this event"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When authorization expires (for AUTH_APPROVED events)"
    )
    
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this event was recorded in our system"
    )
    
    # Additional Data
    raw_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Full raw response from Afterpay"
    )
    
    class Meta:
        verbose_name = 'Afterpay Payment Event'
        verbose_name_plural = 'Afterpay Payment Events'
        ordering = ['-event_created_at']
        indexes = [
            models.Index(fields=['checkout', 'event_type']),
            models.Index(fields=['event_created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - ${self.amount} ({self.event_created_at.strftime('%Y-%m-%d %H:%M')})"


class AfterpayRefund(models.Model):
    """
    Afterpay Refund
    Tracks refunds processed through Afterpay
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    afterpay_refund_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Afterpay's refund ID"
    )
    
    request_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Idempotency key for safe retries"
    )
    
    # Related Checkout
    checkout = models.ForeignKey(
        AfterpayCheckout,
        on_delete=models.CASCADE,
        related_name='refunds',
        help_text="Associated checkout/payment"
    )
    
    # Refund Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Refund amount"
    )
    
    currency = models.CharField(max_length=3)
    
    merchant_reference = models.CharField(
        max_length=255,
        help_text="Merchant's refund reference"
    )
    
    refund_merchant_reference = models.CharField(
        max_length=128,
        blank=True,
        help_text="Unique reference for this refund event"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    refunded_at = models.DateTimeField(
        help_text="When Afterpay processed the refund"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Data
    reason = models.TextField(
        blank=True,
        help_text="Reason for refund"
    )
    
    raw_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Full raw response from Afterpay"
    )
    
    class Meta:
        verbose_name = 'Afterpay Refund'
        verbose_name_plural = 'Afterpay Refunds'
        ordering = ['-refunded_at']
        indexes = [
            models.Index(fields=['checkout', 'status']),
            models.Index(fields=['merchant_reference']),
        ]
    
    def __str__(self):
        return f"Refund {self.merchant_reference} - ${self.amount} ({self.status})"


class AfterpayWebhook(models.Model):
    """
    Afterpay Webhook Event
    Stores incoming webhook events from Afterpay
    """
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Webhook Data
    event_type = models.CharField(
        max_length=100,
        help_text="Type of webhook event"
    )
    
    afterpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Afterpay order ID from webhook"
    )
    
    merchant_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Merchant reference from webhook"
    )
    
    # Processing
    processed = models.BooleanField(
        default=False,
        help_text="Whether this webhook has been processed"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When webhook was processed"
    )
    
    # Payload
    payload = models.JSONField(
        help_text="Full webhook payload"
    )
    
    # Metadata
    received_at = models.DateTimeField(auto_now_add=True)
    
    error_message = models.TextField(
        blank=True,
        help_text="Error message if processing failed"
    )
    
    class Meta:
        verbose_name = 'Afterpay Webhook'
        verbose_name_plural = 'Afterpay Webhooks'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['event_type', 'processed']),
            models.Index(fields=['afterpay_order_id']),
            models.Index(fields=['merchant_reference']),
        ]
    
    def __str__(self):
        status = "✓ Processed" if self.processed else "⧗ Pending"
        return f"{status} {self.event_type} - {self.received_at.strftime('%Y-%m-%d %H:%M')}"
