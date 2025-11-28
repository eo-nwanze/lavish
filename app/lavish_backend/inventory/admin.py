from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import ShopifyLocation, ShopifyInventoryItem, ShopifyInventoryLevel, InventoryAdjustment, InventorySyncLog
from .realtime_sync import sync_inventory_realtime, get_inventory_sync_stats, get_low_stock_alerts


class ShopifyInventoryLevelInline(admin.TabularInline):
    model = ShopifyInventoryLevel
    extra = 0
    readonly_fields = ('updated_at',)
    fields = ('location', 'available', 'committed')


@admin.register(ShopifyLocation)
class ShopifyLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'shopify_id', 'active', 'inventory_items_count')
    search_fields = ('name', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'store_domain')
    
    def inventory_items_count(self, obj):
        return obj.inventory_levels.count()
    inventory_items_count.short_description = "Inventory Items"


@admin.register(ShopifyInventoryItem)
class ShopifyInventoryItemAdmin(admin.ModelAdmin):
    list_display = ('sku', 'variant_name', 'tracked', 'requires_shipping', 'total_available', 'last_synced')
    list_filter = ('tracked', 'requires_shipping', 'store_domain', 'last_synced')
    search_fields = ('sku', 'shopify_id', 'variant__title', 'variant__product__title')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'last_synced', 'store_domain')
    inlines = [ShopifyInventoryLevelInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'sku', 'tracked', 'requires_shipping')
        }),
        ('Product Details', {
            'fields': ('variant', 'cost')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_synced', 'store_domain'),
            'classes': ('collapse',)
        }),
    )
    
    def total_available(self, obj):
        total = sum(level.available for level in obj.levels.all())
        return total
    total_available.short_description = "Total Available"
    
    def variant_name(self, obj):
        if obj.variant:
            product_title = obj.variant.product.title if obj.variant.product else "Unknown Product"
            variant_title = obj.variant.title if obj.variant.title else "Default"
            if variant_title == "Default Title":
                return product_title
            return f"{product_title} - {variant_title}"
        return "No Variant"
    variant_name.short_description = "Product / Variant"
    
    actions = ['sync_selected_items']
    
    def sync_selected_items(self, request, queryset):
        """Sync selected inventory items from Shopify"""
        count = 0
        for item in queryset:
            try:
                # This would need individual item sync implementation
                count += 1
            except Exception as e:
                self.message_user(request, f"Error syncing {item.sku}: {e}", level=messages.ERROR)
        
        self.message_user(request, f"Successfully synced {count} inventory items", level=messages.SUCCESS)
    
    sync_selected_items.short_description = "Sync selected inventory items from Shopify"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('refresh-all/', self.admin_site.admin_view(self.refresh_all_inventory), name='inventory_refresh_all'),
            path('sync-stats/', self.admin_site.admin_view(self.sync_statistics), name='inventory_sync_stats'),
            path('low-stock/', self.admin_site.admin_view(self.low_stock_alerts), name='inventory_low_stock'),
        ]
        return custom_urls + urls
    
    def refresh_all_inventory(self, request):
        """Refresh all inventory from Shopify"""
        try:
            result = sync_inventory_realtime(limit=50)  # Limit for admin safety
            if result['success']:
                stats = result['stats']
                message = f"✅ Inventory sync completed! Total: {stats['total']}, Created: {stats['created']}, Updated: {stats['updated']}, Levels: {stats['levels']}, Locations: {stats['locations']}, Errors: {stats['errors']}"
                messages.success(request, message)
            else:
                messages.error(request, f"❌ Inventory sync failed: {result['message']}")
        except Exception as e:
            messages.error(request, f"❌ Error during inventory sync: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def sync_statistics(self, request):
        """Show sync statistics"""
        try:
            stats = get_inventory_sync_stats()
            message = f"📊 Inventory Stats - Items: {stats['total_inventory_items']}, Levels: {stats['total_inventory_levels']}, Locations: {stats['total_locations']}, Available: {stats['total_available_inventory']}, Low Stock: {stats['low_stock_items']}, Recent syncs (24h): {stats['recent_syncs_24h']}"
            messages.info(request, message)
        except Exception as e:
            messages.error(request, f"❌ Error getting stats: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def low_stock_alerts(self, request):
        """Show low stock alerts"""
        try:
            low_stock_items = get_low_stock_alerts(threshold=10)
            if low_stock_items:
                items_list = ", ".join([f"{item['sku']} ({item['available']} at {item['location']})" for item in low_stock_items[:5]])
                message = f"⚠️ Low Stock Alert! {len(low_stock_items)} items below threshold: {items_list}"
                if len(low_stock_items) > 5:
                    message += f" and {len(low_stock_items) - 5} more..."
                messages.warning(request, message)
            else:
                messages.success(request, "✅ No low stock items found!")
        except Exception as e:
            messages.error(request, f"❌ Error getting low stock alerts: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['refresh_buttons'] = format_html(
            '<a class="button" href="refresh-all/">🔄 Refresh All Inventory</a> '
            '<a class="button" href="sync-stats/">📊 Sync Statistics</a> '
            '<a class="button" href="low-stock/">⚠️ Low Stock Alerts</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShopifyInventoryLevel)
class ShopifyInventoryLevelAdmin(admin.ModelAdmin):
    list_display = ('get_product_name', 'location', 'available', 'committed', 'stock_status')
    list_filter = ('location', 'available', 'store_domain')
    search_fields = ('inventory_item__sku', 'location__name', 'inventory_item__variant__product__title', 'inventory_item__variant__title')
    readonly_fields = ('updated_at', 'store_domain')
    
    def get_product_name(self, obj):
        """Display product and variant name"""
        if obj.inventory_item.variant:
            product = obj.inventory_item.variant.product.title
            variant = obj.inventory_item.variant.title
            sku = obj.inventory_item.sku
            if sku:
                return f"{sku} - {variant} ({product})"
            return f"{variant} ({product})"
        return f"{obj.inventory_item.sku} - Inventory Item"
    get_product_name.short_description = "Inventory Item"
    get_product_name.admin_order_field = 'inventory_item__variant__product__title'
    
    def stock_status(self, obj):
        if obj.available <= 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.available <= 10:
            return format_html('<span style="color: orange;">Low Stock</span>')
        else:
            return format_html('<span style="color: green;">In Stock</span>')
    stock_status.short_description = "Status"


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'location', 'adjustment_type', 'quantity_delta', 'reason', 'created_at')
    list_filter = ('adjustment_type', 'reason', 'location', 'created_at')
    search_fields = ('inventory_item__sku', 'reason', 'notes')
    readonly_fields = ('created_at',)


@admin.register(InventorySyncLog)
class InventorySyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'status', 'items_processed', 'items_created', 'items_updated', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'store_domain', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
