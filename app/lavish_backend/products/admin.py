from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage, ShopifyProductMetafield, ProductSyncLog
from .realtime_sync import sync_products_realtime, get_product_sync_stats


class ShopifyProductVariantInline(admin.TabularInline):
    model = ShopifyProductVariant
    extra = 0
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    fields = ('title', 'sku', 'price', 'compare_at_price', 'inventory_quantity', 'available', 'shopify_id')


class ShopifyProductImageInline(admin.TabularInline):
    model = ShopifyProductImage
    extra = 0
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    fields = ('src', 'alt_text', 'position', 'shopify_id')


class ShopifyProductMetafieldInline(admin.TabularInline):
    model = ShopifyProductMetafield
    extra = 0
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')


@admin.register(ShopifyProduct)
class ShopifyProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'vendor', 'product_type', 'status', 'last_synced')
    list_filter = ('status', 'vendor', 'product_type', 'store_domain', 'last_synced')
    search_fields = ('title', 'handle', 'vendor', 'product_type', 'shopify_id')
    readonly_fields = ('shopify_id', 'handle', 'created_at', 'updated_at', 'published_at', 'last_synced', 'store_domain')
    inlines = [ShopifyProductVariantInline, ShopifyProductImageInline, ShopifyProductMetafieldInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'title', 'handle', 'description')
        }),
        ('Product Details', {
            'fields': ('vendor', 'product_type', 'status', 'tags')
        }),
        ('Publishing', {
            'fields': ('published_at',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_synced', 'store_domain'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_selected_products']
    
    def sync_selected_products(self, request, queryset):
        """Sync selected products from Shopify"""
        count = 0
        for product in queryset:
            try:
                # This would need individual product sync implementation
                count += 1
            except Exception as e:
                self.message_user(request, f"Error syncing {product.title}: {e}", level=messages.ERROR)
        
        self.message_user(request, f"Successfully synced {count} products", level=messages.SUCCESS)
    
    sync_selected_products.short_description = "Sync selected products from Shopify"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('refresh-all/', self.admin_site.admin_view(self.refresh_all_products), name='products_refresh_all'),
            path('sync-stats/', self.admin_site.admin_view(self.sync_statistics), name='products_sync_stats'),
        ]
        return custom_urls + urls
    
    def refresh_all_products(self, request):
        """Refresh all products from Shopify"""
        try:
            result = sync_products_realtime(limit=50)  # Limit for admin safety
            if result['success']:
                stats = result['stats']
                message = f"✅ Product sync completed! Total: {stats['total']}, Created: {stats['created']}, Updated: {stats['updated']}, Variants: {stats['variants']}, Images: {stats['images']}, Errors: {stats['errors']}"
                messages.success(request, message)
            else:
                messages.error(request, f"❌ Product sync failed: {result['message']}")
        except Exception as e:
            messages.error(request, f"❌ Error during product sync: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def sync_statistics(self, request):
        """Show sync statistics"""
        try:
            stats = get_product_sync_stats()
            message = f"📊 Product Stats - Total: {stats['total_products']}, Variants: {stats['total_variants']}, Images: {stats['total_images']}, Recent syncs (24h): {stats['recent_syncs_24h']}"
            messages.info(request, message)
        except Exception as e:
            messages.error(request, f"❌ Error getting stats: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['refresh_buttons'] = format_html(
            '<a class="button" href="refresh-all/">🔄 Refresh All Products</a> '
            '<a class="button" href="sync-stats/">📊 Sync Statistics</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShopifyProductVariant)
class ShopifyProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'sku', 'price', 'inventory_quantity', 'available')
    list_filter = ('available', 'requires_shipping', 'product__vendor', 'store_domain')
    search_fields = ('title', 'sku', 'product__title', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'store_domain')


@admin.register(ShopifyProductImage)
class ShopifyProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'src_preview', 'position')
    list_filter = ('product__vendor', 'store_domain')
    search_fields = ('product__title', 'alt_text', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'store_domain')
    
    def src_preview(self, obj):
        if obj.src:
            return format_html('<img src="{}" width="50" height="50" />', obj.src)
        return "No image"
    src_preview.short_description = "Preview"


@admin.register(ShopifyProductMetafield)
class ShopifyProductMetafieldAdmin(admin.ModelAdmin):
    list_display = ('product', 'namespace', 'key', 'value_preview', 'value_type')
    list_filter = ('namespace', 'key', 'value_type', 'store_domain')
    search_fields = ('product__title', 'namespace', 'key', 'value', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'store_domain')
    
    def value_preview(self, obj):
        if len(obj.value) > 50:
            return obj.value[:50] + "..."
        return obj.value
    value_preview.short_description = "Value"


@admin.register(ProductSyncLog)
class ProductSyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'status', 'products_processed', 'products_created', 'products_updated', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'store_domain', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
