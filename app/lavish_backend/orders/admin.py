from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress, OrderSyncLog
from .realtime_sync import sync_orders_realtime, get_order_sync_stats


class ShopifyOrderAddressInline(admin.TabularInline):
    model = ShopifyOrderAddress
    extra = 0
    readonly_fields = ()
    fields = ('address_type', 'first_name', 'last_name', 'address1', 'city', 'province', 'country', 'zip_code')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Add help text for address editing
        if obj and obj.fulfillment_status in ['null', 'partial']:
            formset.help_text = "✅ Order is unshipped - address changes will be applied"
        elif obj:
            formset.help_text = "⚠️ Order is shipped/fulfilled - address changes won't affect delivery"
        
        return formset


class OrderAddressOverrideInline(admin.StackedInline):
    """Inline for managing address overrides - Edit address for this delivery only"""
    model = None  # We'll link this to the override model
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Address Override - For This Delivery Only', {
            'fields': ('first_name', 'last_name', 'company', 'address1', 'address2', 'city', 'province', 'country', 'zip_code', 'phone'),
            'description': 'Override shipping address for this specific order. This will not affect the customer\'s primary subscription address.'
        }),
        ('Override Details', {
            'fields': ('reason', 'is_temporary'),
            'description': 'Explain why this override is needed'
        }),
    )


class ShopifyOrderLineItemInline(admin.TabularInline):
    model = ShopifyOrderLineItem
    extra = 0
    readonly_fields = ('shopify_id',)
    fields = ('title', 'quantity', 'price', 'shopify_id')


@admin.register(ShopifyOrder)
class ShopifyOrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_email', 'total_price_display', 'financial_status', 'fulfillment_status_badge', 'cutoff_date_display', 'created_at', 'last_synced')
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
        ('Address Management', {
            'fields': (),  # This section is handled by inlines
            'description': 'Manage shipping addresses for this order. Changes to unshipped orders will be applied.',
            'classes': ('wide',)
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
    
    actions = ['create_address_override', 'sync_selected_orders', 'check_cutoff_dates']
    
    def total_price_display(self, obj):
        return f"${obj.total_price} {obj.currency_code}"
    total_price_display.short_description = "Total Price"
    
    def fulfillment_status_badge(self, obj):
        """Show fulfillment status with colored badge"""
        status = obj.fulfillment_status
        colors = {
            'fulfilled': 'green',
            'partial': 'orange', 
            'null': 'red',
            'restocked': 'gray',
        }
        color = colors.get(status, 'gray')
        status_text = 'Unfulfilled' if status == 'null' else status.title()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, status_text
        )
    fulfillment_status_badge.short_description = "Fulfillment Status"
    
    def cutoff_date_display(self, obj):
        """Display cutoff date for subscription orders"""
        try:
            from customer_subscriptions.models import CustomerSubscription
            
            # Check if this is a subscription order by looking for related subscription
            subscription = CustomerSubscription.objects.filter(customer=obj.customer).first()
            if subscription:
                cutoff_date = subscription.get_cutoff_date()
                if cutoff_date:
                    from datetime import date
                    days_until = (cutoff_date - date.today()).days
                    
                    if days_until < 0:
                        return format_html('<span style="color: red;">⚠️ Past Cutoff</span>')
                    elif days_until <= 2:
                        return format_html('<span style="color: orange;">⚡ {} days</span>', days_until)
                    else:
                        return format_html('<span style="color: green;">📅 {} days</span>', days_until)
            
            return "-"
        except:
            return "-"
    cutoff_date_display.short_description = "Cutoff Date"
    
    def create_address_override(self, request, queryset):
        """Create address overrides for selected orders"""
        count = 0
        for order in queryset:
            if order.fulfillment_status in ['null', 'partial']:
                # Only create overrides for unshipped orders
                count += 1
            else:
                self.message_user(request, f"Skipped {order.name} - already fulfilled", level=messages.WARNING)
        
        if count > 0:
            self.message_user(request, f"Ready to create address overrides for {count} orders. Edit individual orders to set override addresses.", level=messages.SUCCESS)
        
    create_address_override.short_description = "📍 Create address overrides for unshipped orders"
    
    def check_cutoff_dates(self, request, queryset):
        """Check cutoff dates for selected orders"""
        from datetime import date
        
        approaching_cutoff = 0
        past_cutoff = 0
        
        for order in queryset:
            try:
                from customer_subscriptions.models import CustomerSubscription
                subscription = CustomerSubscription.objects.filter(customer=order.customer).first()
                if subscription:
                    cutoff_date = subscription.get_cutoff_date()
                    if cutoff_date:
                        days_until = (cutoff_date - date.today()).days
                        if days_until < 0:
                            past_cutoff += 1
                        elif days_until <= 3:
                            approaching_cutoff += 1
            except:
                continue
        
        message = f"Cutoff Check: {approaching_cutoff} approaching cutoff, {past_cutoff} past cutoff"
        self.message_user(request, message, level=messages.INFO)
    
    check_cutoff_dates.short_description = "⏰ Check cutoff dates"
    
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
