"""
Admin interface for Subscription Skip management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from customer_subscriptions.models import CustomerSubscription
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import (
    SubscriptionSkipPolicy,
    SubscriptionSkip,
    SkipNotification,
    SkipAnalytics
)


# Import-Export Resources
class SubscriptionSkipPolicyResource(resources.ModelResource):
    class Meta:
        model = SubscriptionSkipPolicy
        import_id_fields = ['id']


class SubscriptionSkipResource(resources.ModelResource):
    class Meta:
        model = SubscriptionSkip
        import_id_fields = ['id']


class SkipNotificationResource(resources.ModelResource):
    class Meta:
        model = SkipNotification
        import_id_fields = ['id']


class SkipAnalyticsResource(resources.ModelResource):
    class Meta:
        model = SkipAnalytics
        import_id_fields = ['id']


@admin.register(SubscriptionSkipPolicy)
class SubscriptionSkipPolicyAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionSkipPolicyResource
    list_display = ('name', 'max_skips_per_year', 'max_consecutive_skips', 
                    'advance_notice_days', 'skip_fee', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('name', 'is_active')
        }),
        ('Skip Limits', {
            'fields': ('max_skips_per_year', 'max_consecutive_skips', 'advance_notice_days')
        }),
        ('Pricing', {
            'fields': ('skip_fee',)
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class SubscriptionSkipInline(admin.TabularInline):
    model = SubscriptionSkip
    extra = 0
    fields = ('original_order_date', 'new_order_date', 'status', 'skip_type', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False
    show_change_link = True


# CustomerSubscription is registered in customer_subscriptions.admin
# No separate registration needed here - it's managed by the main app


@admin.register(SubscriptionSkip)
class SubscriptionSkipAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionSkipResource
    list_display = ('subscription_link', 'original_order_date', 'new_order_date', 
                    'status_badge', 'skip_type', 'shopify_synced', 'created_at')
    list_filter = ('status', 'skip_type', 'shopify_synced', 'created_at')
    search_fields = ('subscription__customer_email', 'subscription__subscription_name',
                     'shopify_order_id', 'reason')
    readonly_fields = ('created_at', 'confirmed_at', 'cancelled_at', 'subscription')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Subscription', {
            'fields': ('subscription',)
        }),
        ('Skip Details', {
            'fields': ('skip_type', 'status', 'reason', 'reason_details')
        }),
        ('Schedule Changes', {
            'fields': (('original_order_date', 'original_billing_date'),
                      ('new_order_date', 'new_billing_date'))
        }),
        ('Financial', {
            'fields': ('skip_fee_charged', 'refund_issued')
        }),
        ('Shopify Integration', {
            'fields': ('shopify_order_id', 'shopify_synced', 'shopify_sync_error')
        }),
        ('Administration', {
            'fields': ('admin_notes', 'processed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def subscription_link(self, obj):
        url = reverse('admin:customer_subscriptions_customersubscription_change', args=[obj.subscription.pk])
        return format_html('<a href="{}">{}</a>', url, obj.subscription)
    subscription_link.short_description = 'Subscription'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'confirmed': '#28A745',
            'cancelled': '#DC3545',
            'failed': '#6C757D'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    actions = ['confirm_skips', 'cancel_skips', 'sync_to_shopify', 'send_skip_notifications']
    
    def confirm_skips(self, request, queryset):
        confirmed = 0
        errors = []
        for skip in queryset.filter(status='pending'):
            try:
                skip.confirm_skip()
                
                # Send notification via email_manager
                from .notification_service import SkipNotificationService
                SkipNotificationService.send_skip_confirmed_notification(skip, skip.subscription)
                
                confirmed += 1
            except Exception as e:
                errors.append(f"Skip {skip.pk}: {str(e)}")
        
        self.message_user(request, f'Confirmed {confirmed} skip(s)')
        if errors:
            self.message_user(request, f'Errors: {", ".join(errors)}', level='error')
    confirm_skips.short_description = 'Confirm selected skips'
    
    def cancel_skips(self, request, queryset):
        cancelled = 0
        for skip in queryset.filter(status='pending'):
            try:
                skip.cancel_skip(reason="Cancelled by admin")
                cancelled += 1
            except Exception as e:
                pass
        self.message_user(request, f'Cancelled {cancelled} skip(s)')
    cancel_skips.short_description = 'Cancel selected skips'
    
    def sync_to_shopify(self, request, queryset):
        # Placeholder for Shopify sync functionality
        count = queryset.filter(status='confirmed', shopify_synced=False).count()
        self.message_user(request, f'Would sync {count} skip(s) to Shopify (not implemented yet)')
    sync_to_shopify.short_description = 'Sync to Shopify'
    
    def send_skip_notifications(self, request, queryset):
        """Send email notifications for selected skips"""
        from .notification_service import SkipNotificationService
        
        sent = 0
        failed = 0
        
        for skip in queryset.filter(status='confirmed'):
            try:
                success = SkipNotificationService.send_skip_confirmed_notification(skip, skip.subscription)
                if success:
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.message_user(request, f'Error sending notification for skip {skip.pk}: {str(e)}', level='error')
        
        if sent > 0:
            self.message_user(request, f'Successfully sent {sent} notification(s)', level='success')
        if failed > 0:
            self.message_user(request, f'Failed to send {failed} notification(s)', level='warning')
    
    send_skip_notifications.short_description = 'Send email notifications'


@admin.register(SkipNotification)
class SkipNotificationAdmin(ImportExportModelAdmin):
    resource_class = SkipNotificationResource
    list_display = ('notification_type', 'channel', 'recipient_email', 
                    'delivered_badge', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'channel', 'delivered', 'sent_at')
    search_fields = ('recipient_email', 'recipient_phone', 'subject')
    readonly_fields = ('created_at', 'sent_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('notification_type', 'channel')
        }),
        ('Related Records', {
            'fields': ('skip', 'subscription')
        }),
        ('Recipient', {
            'fields': ('recipient_email', 'recipient_phone')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Delivery Status', {
            'fields': ('sent_at', 'delivered', 'error_message')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def delivered_badge(self, obj):
        if obj.delivered:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Delivered</span>'
            )
        elif obj.sent_at:
            return format_html(
                '<span style="color: orange;">⧗ Sent</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Not Sent</span>'
            )
    delivered_badge.short_description = 'Delivery Status'
    
    actions = ['resend_notifications', 'mark_as_delivered']
    
    def resend_notifications(self, request, queryset):
        """Resend failed or unsent notifications"""
        from .notification_service import SkipNotificationService
        
        sent = 0
        failed = 0
        
        for notification in queryset.filter(delivered=False):
            try:
                if notification.skip:
                    success = SkipNotificationService.send_skip_confirmed_notification(
                        notification.skip, 
                        notification.subscription
                    )
                elif notification.notification_type == 'skip_reminder':
                    success = SkipNotificationService.send_skip_reminder_notification(
                        notification.subscription,
                        days_until_cutoff=7  # Default to 7 days
                    )
                elif notification.notification_type == 'skip_limit_reached':
                    success = SkipNotificationService.send_skip_limit_reached_notification(
                        notification.subscription
                    )
                else:
                    success = False
                
                if success:
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
        
        if sent > 0:
            self.message_user(request, f'Successfully resent {sent} notification(s)', level='success')
        if failed > 0:
            self.message_user(request, f'Failed to resend {failed} notification(s)', level='warning')
    
    resend_notifications.short_description = 'Resend failed notifications'
    
    def mark_as_delivered(self, request, queryset):
        """Mark selected notifications as delivered"""
        count = queryset.update(delivered=True)
        self.message_user(request, f'Marked {count} notification(s) as delivered')
    
    mark_as_delivered.short_description = 'Mark as delivered'


@admin.register(SkipAnalytics)
class SkipAnalyticsAdmin(ImportExportModelAdmin):
    resource_class = SkipAnalyticsResource
    list_display = ('period_type', 'period_start', 'period_end', 
                    'total_skips', 'confirmed_skips', 'unique_customers',
                    'revenue_deferred', 'generated_at')
    list_filter = ('period_type', 'period_start')
    readonly_fields = ('generated_at',)
    date_hierarchy = 'period_start'
    
    fieldsets = (
        ('Period', {
            'fields': ('period_type', 'period_start', 'period_end')
        }),
        ('Skip Metrics', {
            'fields': ('total_skips', 'confirmed_skips', 'cancelled_skips', 'failed_skips')
        }),
        ('Customer Metrics', {
            'fields': ('unique_customers', 'new_skippers', 'repeat_skippers')
        }),
        ('Financial Impact', {
            'fields': ('revenue_deferred', 'skip_fees_collected')
        }),
        ('Insights', {
            'fields': ('top_reasons',)
        }),
        ('Metadata', {
            'fields': ('store_domain', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Analytics should be generated by system, not manually added
        return False
