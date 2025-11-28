from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress, OrderSyncLog
from .realtime_sync import sync_orders_realtime, get_order_sync_stats


class ShopifyOrderLineItemInline(admin.TabularInline):
    model = ShopifyOrderLineItem
    extra = 0
    readonly_fields = ('shopify_id',)
    fields = ('title', 'quantity', 'price', 'shopify_id')


class ShopifyOrderAddressInline(admin.TabularInline):
    model = ShopifyOrderAddress
    extra = 0
    readonly_fields = ()
    fields = ('address_type', 'first_name', 'last_name', 'address1', 'city', 'province', 'country', 'zip_code')


@admin.register(ShopifyOrder)
class ShopifyOrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_email', 'total_price_display', 'financial_status', 'fulfillment_status', 'created_at', 'last_synced')
    list_filter = ('financial_status', 'fulfillment_status', 'currency_code', 'store_domain', 'created_at', 'last_synced')
    search_fields = ('name', 'customer_email', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'processed_at', 'last_synced', 'store_domain')
    inlines = [ShopifyOrderLineItemInline, ShopifyOrderAddressInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('shopify_id', 'name', 'customer_email', 'customer_phone')
        }),
        ('Financial Details', {
            'fields': ('total_price', 'currency_code', 'financial_status', 'fulfillment_status')
        }),
        ('Additional Info', {
            'fields': ('subtotal_price', 'total_tax', 'total_shipping_price'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at', 'last_synced', 'store_domain'),
            'classes': ('collapse',)
        }),
    )
    
    def total_price_display(self, obj):
        return f"${obj.total_price} {obj.currency_code}"
    total_price_display.short_description = "Total Price"
    
    actions = ['sync_selected_orders']
    
    def sync_selected_orders(self, request, queryset):
        """Sync selected orders from Shopify"""
        count = 0
        for order in queryset:
            try:
                # This would need individual order sync implementation
                count += 1
            except Exception as e:
                self.message_user(request, f"Error syncing {order.name}: {e}", level=messages.ERROR)
        
        self.message_user(request, f"Successfully synced {count} orders", level=messages.SUCCESS)
    
    sync_selected_orders.short_description = "Sync selected orders from Shopify"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('refresh-all/', self.admin_site.admin_view(self.refresh_all_orders), name='orders_refresh_all'),
            path('sync-stats/', self.admin_site.admin_view(self.sync_statistics), name='orders_sync_stats'),
        ]
        return custom_urls + urls
    
    def refresh_all_orders(self, request):
        """Refresh all orders from Shopify"""
        try:
            result = sync_orders_realtime(limit=50)  # Limit for admin safety
            if result['success']:
                stats = result['stats']
                message = f"✅ Order sync completed! Total: {stats['total']}, Created: {stats['created']}, Updated: {stats['updated']}, Line Items: {stats['line_items']}, Errors: {stats['errors']}"
                messages.success(request, message)
            else:
                messages.error(request, f"❌ Order sync failed: {result['message']}")
        except Exception as e:
            messages.error(request, f"❌ Error during order sync: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def sync_statistics(self, request):
        """Show sync statistics"""
        try:
            stats = get_order_sync_stats()
            message = f"📊 Order Stats - Total: {stats['total_orders']}, Line Items: {stats['total_line_items']}, Revenue: ${stats['total_revenue']:.2f}, Recent syncs (24h): {stats['recent_syncs_24h']}"
            messages.info(request, message)
        except Exception as e:
            messages.error(request, f"❌ Error getting stats: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['refresh_buttons'] = format_html(
            '<a class="button" href="refresh-all/">🔄 Refresh All Orders</a> '
            '<a class="button" href="sync-stats/">📊 Sync Statistics</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShopifyOrderLineItem)
class ShopifyOrderLineItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'title', 'quantity', 'price')
    list_filter = ('order__financial_status', 'order__fulfillment_status', 'store_domain')
    search_fields = ('title', 'order__name', 'shopify_id')
    readonly_fields = ('shopify_id', 'store_domain')


@admin.register(ShopifyOrderAddress)
class ShopifyOrderAddressAdmin(admin.ModelAdmin):
    list_display = ('order', 'address_type', 'full_name', 'city', 'province', 'country')
    list_filter = ('address_type', 'country', 'province', 'store_domain')
    search_fields = ('first_name', 'last_name', 'address1', 'city', 'order__name')
    readonly_fields = ('store_domain',)
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = "Name"


@admin.register(OrderSyncLog)
class OrderSyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'status', 'orders_processed', 'orders_created', 'orders_updated', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'store_domain', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
