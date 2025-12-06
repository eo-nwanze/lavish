from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage, ShopifyProductMetafield, ProductSyncLog
from .realtime_sync import sync_products_realtime, get_product_sync_stats
from .bidirectional_sync import ProductBidirectionalSync


# Import-Export Resources
class ShopifyProductResource(resources.ModelResource):
    class Meta:
        model = ShopifyProduct
        import_id_fields = ['shopify_id']


class ShopifyProductVariantResource(resources.ModelResource):
    class Meta:
        model = ShopifyProductVariant
        import_id_fields = ['shopify_id']


class ShopifyProductImageResource(resources.ModelResource):
    class Meta:
        model = ShopifyProductImage
        import_id_fields = ['shopify_id']


class ShopifyProductMetafieldResource(resources.ModelResource):
    class Meta:
        model = ShopifyProductMetafield
        import_id_fields = ['shopify_id']


class ProductSyncLogResource(resources.ModelResource):
    class Meta:
        model = ProductSyncLog
        import_id_fields = ['id']


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


class ShippingConfigInline(admin.StackedInline):
    """Inline for Product Shipping Configuration - Cutoff logic and shipping settings"""
    from customer_subscriptions.models import ProductShippingConfig
    model = ProductShippingConfig
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Cutoff Configuration', {
            'fields': ('cutoff_days', 'reminder_days'),
            'description': 'Configure when orders are cut off and when reminders are sent before shipping'
        }),
        ('Shipping Details', {
            'fields': ('processing_days', 'estimated_transit_days')
        }),
        ('Special Handling', {
            'fields': ('special_handling', 'handling_notes')
        }),
        ('International Shipping', {
            'fields': ('international_shipping', 'restricted_countries'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShopifyProduct)
class ShopifyProductAdmin(ImportExportModelAdmin):
    resource_class = ShopifyProductResource
    list_display = ('title', 'vendor', 'product_type', 'status_badge', 'cutoff_days_display', 'sync_status_badge', 'last_synced')
    list_filter = ('status', 'vendor', 'product_type', 'created_in_django', 'needs_shopify_push', 'store_domain', 'last_synced')
    search_fields = ('title', 'handle', 'vendor', 'product_type', 'shopify_id')
    readonly_fields = ('handle', 'created_at', 'updated_at', 'published_at', 'last_synced', 'last_pushed_to_shopify', 'store_domain', 'shopify_push_error')
    inlines = [ShopifyProductVariantInline, ShopifyProductImageInline, ShopifyProductMetafieldInline, ShippingConfigInline]
    
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
        ('Shipping Configuration', {
            'fields': (),  # This section is handled by inlines
            'description': 'Configure cutoff dates and shipping settings for this product'
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',)
        }),
        ('Sync Status', {
            'fields': ('created_in_django', 'needs_shopify_push', 'shopify_push_error', 'sync_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_synced', 'last_pushed_to_shopify', 'store_domain'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_selected_products', 'push_to_shopify', 'update_in_shopify', 'delete_from_shopify', 'mark_for_push', 'create_shipping_configs']
    
    def save_model(self, request, obj, form, change):
        """Auto-push to Shopify on create/update"""
        from django.utils import timezone
        
        # For new products, ensure timestamps are set
        if not change:
            if not obj.created_at:
                obj.created_at = timezone.now()
            if not obj.updated_at:
                obj.updated_at = timezone.now()
            # Generate handle if not provided
            if not obj.handle:
                obj.handle = obj.title.lower().replace(' ', '-').replace('/', '-')
            # Set shopify_id for new products (will be updated after Shopify push)
            if not obj.shopify_id:
                obj.shopify_id = f"temp_{int(timezone.now().timestamp())}"
        
        super().save_model(request, obj, form, change)
        
        # Auto-push to Shopify if flagged
        if obj.needs_shopify_push:
            # Skip test/temp products
            if not (obj.shopify_id and (obj.shopify_id.startswith('test_') or obj.shopify_id.startswith('temp_'))):
                sync_service = ProductBidirectionalSync()
                result = sync_service.push_product_to_shopify(obj)
                
                if result.get('success'):
                    self.message_user(request, f"✅ Product synced to Shopify: {obj.title}", level=messages.SUCCESS)
                else:
                    self.message_user(request, f"⚠️ Product saved locally but Shopify sync failed: {result.get('message', 'Unknown error')}", level=messages.WARNING)
            else:
                # For temp products, still save but don't push
                self.message_user(request, f"ℹ️ Product saved with temporary ID. Will be pushed to Shopify on next update.", level=messages.INFO)
    
    def save_formset(self, request, form, formset, change):
        """Save variants and auto-push to Shopify"""
        instances = formset.save(commit=False)
        
        # Process deleted objects
        for obj in formset.deleted_objects:
            obj.delete()
        
        # Process new/updated instances
        for instance in instances:
            instance.save()
        
        # Save many-to-many relationships
        formset.save_m2m()
        
        # If this is a variant formset and product exists, mark product for sync
        if formset.model == ShopifyProductVariant:
            product = form.instance
            if product.pk and product.shopify_id:
                # Mark product for push if it has variants
                if not product.shopify_id.startswith('temp_'):
                    product.needs_shopify_push = True
                    product.save(update_fields=['needs_shopify_push'])
    
    def delete_model(self, request, obj):
        """Auto-delete from Shopify on delete"""
        product_title = obj.title
        product_id = obj.shopify_id
        
        # Try to delete from Shopify if it has a Shopify ID
        if product_id and not (product_id.startswith('test_') or product_id.startswith('temp_')):
            sync_service = ProductBidirectionalSync()
            result = sync_service.delete_product_from_shopify(obj)
            
            if result.get('success'):
                self.message_user(request, f"✅ Product '{product_title}' deleted from both Django and Shopify", level=messages.SUCCESS)
            else:
                self.message_user(request, f"⚠️ Product '{product_title}' deleted from Django but Shopify delete failed: {result.get('message', 'Unknown error')}", level=messages.WARNING)
        else:
            self.message_user(request, f"ℹ️ Product '{product_title}' deleted from Django only (no Shopify ID)", level=messages.INFO)
        
        super().delete_model(request, obj)
    
    def status_badge(self, obj):
        """Show product status with colored badge"""
        colors = {
            'ACTIVE': 'green',
            'ARCHIVED': 'gray',
            'DRAFT': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = "Status"
    
    def cutoff_days_display(self, obj):
        """Display cutoff days for product shipping"""
        try:
            if hasattr(obj, 'shipping_config'):
                config = obj.shipping_config
                if config.cutoff_days <= 3:
                    return format_html('<span style="color: red;">⚡ {} days</span>', config.cutoff_days)
                elif config.cutoff_days <= 7:
                    return format_html('<span style="color: orange;">⏰ {} days</span>', config.cutoff_days)
                else:
                    return format_html('<span style="color: green;">📅 {} days</span>', config.cutoff_days)
            return format_html('<span style="color: gray;">📋 Setup needed</span>')
        except:
            return "-"
    cutoff_days_display.short_description = "Cutoff Days"
    
    def sync_status_badge(self, obj):
        """Show sync status badge"""
        if obj.created_in_django and obj.needs_shopify_push:
            return format_html('<span style="color: orange;">⏳ Pending Push</span>')
        elif obj.created_in_django and obj.shopify_id:
            return format_html('<span style="color: green;">✅ Synced</span>')
        elif obj.created_in_django:
            return format_html('<span style="color: red;">❌ Not Synced</span>')
        else:
            return format_html('<span style="color: blue;">📥 From Shopify</span>')
    sync_status_badge.short_description = "Sync Status"
    
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
    
    sync_selected_products.short_description = "📥 Sync selected products FROM Shopify"
    
    def push_to_shopify(self, request, queryset):
        """Push selected products TO Shopify (create new or update existing)"""
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for product in queryset:
            result = bidirectional_sync.push_product_to_shopify(product)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{product.title}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully pushed {results['successful']} products to Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to push {results['failed']} products. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    push_to_shopify.short_description = "📤 Push selected products TO Shopify (Create/Update)"
    
    def update_in_shopify(self, request, queryset):
        """Update existing products in Shopify"""
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for product in queryset:
            if not product.shopify_id:
                results["failed"] += 1
                results["errors"].append(f"{product.title}: No Shopify ID (use 'Push to Shopify' instead)")
                continue
            
            result = bidirectional_sync.push_product_to_shopify(product)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{product.title}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully updated {results['successful']} products in Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to update {results['failed']} products. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    update_in_shopify.short_description = "🔄 Update existing products IN Shopify"
    
    def delete_from_shopify(self, request, queryset):
        """Delete selected products from Shopify"""
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for product in queryset:
            if not product.shopify_id:
                results["failed"] += 1
                results["errors"].append(f"{product.title}: No Shopify ID, cannot delete")
                continue
            
            result = bidirectional_sync.delete_product_from_shopify(product)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{product.title}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully deleted {results['successful']} products from Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to delete {results['failed']} products. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    delete_from_shopify.short_description = "🗑️ Delete selected products FROM Shopify"
    
    def mark_for_push(self, request, queryset):
        """Mark selected products as needing push to Shopify"""
        count = queryset.update(needs_shopify_push=True)
        self.message_user(request, f"✅ Marked {count} products for push to Shopify", level=messages.SUCCESS)
    
    mark_for_push.short_description = "⚡ Mark for push to Shopify"
    
    def create_shipping_configs(self, request, queryset):
        """Create default shipping configs for selected products"""
        from customer_subscriptions.models import ProductShippingConfig
        
        created = 0
        skipped = 0
        
        for product in queryset:
            config, was_created = ProductShippingConfig.objects.get_or_create(
                product=product,
                defaults={
                    'cutoff_days': 7,
                    'reminder_days': 14,
                    'processing_days': 2,
                    'estimated_transit_days': 5,
                    'international_shipping': True,
                    'special_handling': False,
                }
            )
            
            if was_created:
                created += 1
            else:
                skipped += 1
        
        message = f"Created shipping configs for {created} products"
        if skipped > 0:
            message += f", skipped {skipped} (already configured)"
        
        self.message_user(request, message, level=messages.SUCCESS)
    
    create_shipping_configs.short_description = "📦 Create default shipping configs"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('refresh-all/', self.admin_site.admin_view(self.refresh_all_products), name='products_refresh_all'),
            path('sync-stats/', self.admin_site.admin_view(self.sync_statistics), name='products_sync_stats'),
            path('push-pending/', self.admin_site.admin_view(self.push_pending_products), name='products_push_pending'),
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
    
    def push_pending_products(self, request):
        """Push all products marked as needing push to Shopify"""
        try:
            results = bidirectional_sync.sync_pending_products()
            if results['successful'] > 0:
                message = f"✅ Push completed! Successful: {results['successful']}/{results['total']}"
                messages.success(request, message)
            
            if results['failed'] > 0:
                error_msg = f"❌ Failed: {results['failed']}/{results['total']}. Check product sync errors for details."
                messages.warning(request, error_msg)
                
            if results['total'] == 0:
                messages.info(request, "ℹ️ No products marked for push to Shopify")
        except Exception as e:
            messages.error(request, f"❌ Error during push: {str(e)}")
        
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
            '<a class="button" href="refresh-all/">📥 Refresh FROM Shopify</a> '
            '<a class="button" href="push-pending/">📤 Push TO Shopify</a> '
            '<a class="button" href="sync-stats/">📊 Sync Statistics</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShopifyProductVariant)
class ShopifyProductVariantAdmin(ImportExportModelAdmin):
    resource_class = ShopifyProductVariantResource
    list_display = ('product', 'title', 'sku', 'price', 'inventory_quantity', 'available')
    list_filter = ('available', 'requires_shipping', 'product__vendor', 'store_domain')
    search_fields = ('title', 'sku', 'product__title', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'store_domain')


@admin.register(ShopifyProductImage)
class ShopifyProductImageAdmin(ImportExportModelAdmin):
    resource_class = ShopifyProductImageResource
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
class ShopifyProductMetafieldAdmin(ImportExportModelAdmin):
    resource_class = ShopifyProductMetafieldResource
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
class ProductSyncLogAdmin(ImportExportModelAdmin):
    resource_class = ProductSyncLogResource
    list_display = ('operation_type', 'status', 'products_processed', 'products_created', 'products_updated', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'store_domain', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
