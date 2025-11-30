"""
Subscription Skip Models

Manages customer subscription skips, allowing them to temporarily pause
their next delivery/payment without cancelling their subscription.
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class SubscriptionSkipPolicy(models.Model):
    """
    Defines skip policies for subscriptions
    Configurable per subscription or customer type
    """
    
    name = models.CharField(max_length=100, help_text="Policy name (e.g., 'Standard Skip Policy')")
    max_skips_per_year = models.IntegerField(default=4, help_text="Maximum skips allowed per calendar year")
    max_consecutive_skips = models.IntegerField(default=2, help_text="Maximum consecutive skips allowed")
    advance_notice_days = models.IntegerField(default=7, help_text="Days before next order customer must skip")
    skip_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Fee charged for skipping")
    is_active = models.BooleanField(default=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Skip Policy'
        verbose_name_plural = 'Skip Policies'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (Max: {self.max_skips_per_year}/year)"


class SubscriptionSkip(models.Model):
    """
    Records each skip action taken by a customer
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    SKIP_TYPE_CHOICES = [
        ('manual', 'Manual Customer Request'),
        ('auto', 'Automatic System Skip'),
        ('admin', 'Admin Override'),
    ]
    
    subscription = models.ForeignKey('customer_subscriptions.CustomerSubscription', on_delete=models.CASCADE, 
                                      related_name='skips')
    
    # Skip Details
    skip_type = models.CharField(max_length=20, choices=SKIP_TYPE_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Original and New Dates
    original_order_date = models.DateField(help_text="Original scheduled order date")
    original_billing_date = models.DateField(help_text="Original billing date")
    new_order_date = models.DateField(help_text="New rescheduled order date")
    new_billing_date = models.DateField(help_text="New rescheduled billing date")
    
    # Skip Reason
    reason = models.CharField(max_length=100, blank=True, help_text="Customer-provided reason")
    reason_details = models.TextField(blank=True, help_text="Additional details")
    
    # Financial
    skip_fee_charged = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    refund_issued = models.BooleanField(default=False, help_text="Whether any refund was issued")
    
    # Shopify Integration
    shopify_order_id = models.CharField(max_length=255, blank=True, null=True, 
                                         help_text="Shopify order ID that was skipped")
    shopify_synced = models.BooleanField(default=False, help_text="Whether skip synced to Shopify")
    shopify_sync_error = models.TextField(blank=True, help_text="Error message if sync failed")
    
    # Admin Notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes about this skip")
    processed_by = models.CharField(max_length=100, blank=True, help_text="Staff member who processed")
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now, help_text="When skip was requested")
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When skip was confirmed")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="If skip was cancelled")
    
    class Meta:
        verbose_name = 'Subscription Skip'
        verbose_name_plural = 'Subscription Skips'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['original_order_date']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Skip {self.original_order_date} → {self.new_order_date} ({self.status})"
    
    def confirm_skip(self):
        """Confirm and apply the skip"""
        if self.status != 'pending':
            raise ValidationError(f"Can only confirm pending skips. Current status: {self.status}")
        
        # Update subscription
        self.subscription.next_order_date = self.new_order_date
        self.subscription.next_billing_date = self.new_billing_date
        self.subscription.skips_used_this_year += 1
        self.subscription.consecutive_skips += 1
        self.subscription.save()
        
        # Update skip record
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def cancel_skip(self, reason=""):
        """Cancel a pending skip"""
        if self.status != 'pending':
            raise ValidationError(f"Can only cancel pending skips. Current status: {self.status}")
        
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if reason:
            self.admin_notes += f"\nCancelled: {reason}"
        self.save()


class SkipNotification(models.Model):
    """
    Tracks notifications sent about skips
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('skip_confirmed', 'Skip Confirmed'),
        ('skip_reminder', 'Skip Reminder'),
        ('skip_expiring', 'Skips Expiring'),
        ('skip_limit_reached', 'Skip Limit Reached'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    skip = models.ForeignKey(SubscriptionSkip, on_delete=models.CASCADE, 
                              related_name='notifications', null=True, blank=True)
    subscription = models.ForeignKey('customer_subscriptions.CustomerSubscription', on_delete=models.CASCADE,
                                      related_name='skip_notifications')
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Skip Notification'
        verbose_name_plural = 'Skip Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient_email} ({self.sent_at or 'Not sent'})"


class SkipAnalytics(models.Model):
    """
    Aggregated analytics about skip behavior
    Generated periodically for reporting
    """
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Skip Metrics
    total_skips = models.IntegerField(default=0)
    confirmed_skips = models.IntegerField(default=0)
    cancelled_skips = models.IntegerField(default=0)
    failed_skips = models.IntegerField(default=0)
    
    # Customer Metrics
    unique_customers = models.IntegerField(default=0)
    new_skippers = models.IntegerField(default=0, help_text="Customers skipping for first time")
    repeat_skippers = models.IntegerField(default=0)
    
    # Financial Impact
    revenue_deferred = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    skip_fees_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Skip Reasons (Top 5)
    top_reasons = models.JSONField(default=dict, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    generated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Skip Analytics'
        verbose_name_plural = 'Skip Analytics'
        ordering = ['-period_start']
        unique_together = ['period_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.period_type.title()} Skip Analytics ({self.period_start} to {self.period_end})"
