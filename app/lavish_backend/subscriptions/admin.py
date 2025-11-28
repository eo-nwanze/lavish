from django.contrib import admin
from django.utils.html import format_html
from .models import ShopifyWebhookSubscription, ShopifyWebhookDelivery, ShopifyWebhookSyncLog


@admin.register(ShopifyWebhookSubscription)
class ShopifyWebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('topic_display', 'uri_short', 'format', 'endpoint_type', 'status_badge', 'api_version', 'created_at')
    list_filter = ('topic', 'format', 'endpoint_type', 'is_active', 'created_at')
    search_fields = ('shopify_id', 'topic', 'uri', 'filter_query')
    readonly_fields = ('shopify_id', 'legacy_resource_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('shopify_id', 'legacy_resource_id', 'topic', 'format', 'api_version')
        }),
        ('Endpoint Configuration', {
            'fields': ('endpoint_type', 'uri')
        }),
        ('Filtering & Customization', {
            'fields': ('filter_query', 'include_fields', 'metafield_namespaces'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def topic_display(self, obj):
        icon_map = {
            'orders': '🛒',
            'products': '📦',
            'customers': '👥',
            'inventory': '📊',
            'fulfillments': '🚚',
            'refunds': '💰',
            'collections': '📚',
            'app': '📱',
            'shop': '🏪',
            'checkouts': '🛍️',
            'disputes': '⚠️',
        }
        category = obj.topic.split('/')[0] if '/' in obj.topic else 'other'
        icon = icon_map.get(category, '📌')
        return format_html(
            '<span style="font-size: 14px;">{} {}</span>',
            icon, obj.get_topic_display()
        )
    topic_display.short_description = 'Topic'
    
    def uri_short(self, obj):
        if len(obj.uri) > 50:
            return format_html(
                '<span title="{}">{}</span>',
                obj.uri, obj.uri[:47] + '...'
            )
        return obj.uri
    uri_short.short_description = 'Destination URI'
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'


@admin.register(ShopifyWebhookDelivery)
class ShopifyWebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ('subscription_topic', 'status_badge', 'response_code', 'retry_count', 'attempted_at', 'duration')
    list_filter = ('status', 'response_code', 'attempted_at')
    search_fields = ('delivery_id', 'subscription__topic', 'error_message')
    readonly_fields = ('delivery_id', 'attempted_at', 'completed_at', 'created_at')
    date_hierarchy = 'attempted_at'
    
    fieldsets = (
        ('Delivery Info', {
            'fields': ('delivery_id', 'subscription', 'status')
        }),
        ('Request/Response', {
            'fields': ('request_payload', 'response_code', 'response_body', 'error_message')
        }),
        ('Timing', {
            'fields': ('attempted_at', 'completed_at', 'retry_count')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subscription_topic(self, obj):
        return obj.subscription.topic
    subscription_topic.short_description = 'Topic'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'success': 'green',
            'failed': 'red',
            'retrying': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.title()
        )
    status_badge.short_description = 'Status'
    
    def duration(self, obj):
        if obj.completed_at and obj.attempted_at:
            delta = obj.completed_at - obj.attempted_at
            return f"{delta.total_seconds():.2f}s"
        return "N/A"
    duration.short_description = 'Duration'


@admin.register(ShopifyWebhookSyncLog)
class ShopifyWebhookSyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'status_badge', 'stats_display', 'started_at', 'duration')
    list_filter = ('operation_type', 'status', 'started_at')
    search_fields = ('error_message',)
    readonly_fields = ('started_at', 'completed_at')
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation_type', 'status')
        }),
        ('Statistics', {
            'fields': ('subscriptions_synced', 'subscriptions_created', 'subscriptions_updated', 'subscriptions_deleted')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'in_progress': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'
    
    def stats_display(self, obj):
        return format_html(
            'Synced: {} | Created: {} | Updated: {} | Deleted: {}',
            obj.subscriptions_synced,
            obj.subscriptions_created,
            obj.subscriptions_updated,
            obj.subscriptions_deleted
        )
    stats_display.short_description = 'Statistics'
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.2f}s"
        return "In Progress" if obj.status == 'in_progress' else "N/A"
    duration.short_description = 'Duration'
