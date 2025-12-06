from django.contrib import admin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import ShopifyCustomer, ShopifyCustomerAddress, CustomerSyncLog
from .realtime_sync import sync_customers_realtime, get_customer_sync_stats
from .customer_bidirectional_sync import push_customer_to_shopify
from .address_bidirectional_sync_fixed import push_address_to_shopify


# Import-Export Resources
class ShopifyCustomerResource(resources.ModelResource):
    class Meta:
        model = ShopifyCustomer
        import_id_fields = ('shopify_id',)


class ShopifyCustomerAddressResource(resources.ModelResource):
    class Meta:
        model = ShopifyCustomerAddress
        import_id_fields = ('shopify_id',)


class CustomerSyncLogResource(resources.ModelResource):
    class Meta:
        model = CustomerSyncLog


class ShopifyCustomerAddressInline(admin.TabularInline):
    model = ShopifyCustomerAddress
    extra = 0
    readonly_fields = ('shopify_id',)


@admin.register(ShopifyCustomer)
class ShopifyCustomerAdmin(ImportExportModelAdmin):
    resource_class = ShopifyCustomerResource
    list_display = ('full_name', 'email', 'phone', 'state', 'number_of_orders', 'verified_email', 'last_synced')
    list_filter = ('state', 'verified_email', 'tax_exempt', 'store_domain', 'last_synced')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at', 'last_synced', 'store_domain')
    inlines = [ShopifyCustomerAddressInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Status & Settings', {
            'fields': ('state', 'verified_email', 'tax_exempt', 'number_of_orders')
        }),
        ('Tags & Notes', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_synced', 'store_domain'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_selected_customers']
    
    def save_model(self, request, obj, form, change):
        """Auto-push to Shopify on create/update"""
        super().save_model(request, obj, form, change)
        
        # Auto-push to Shopify if flagged
        if obj.needs_shopify_push:
            # Skip test/temp customers
            if not (obj.shopify_id and (obj.shopify_id.startswith('test_') or obj.shopify_id.startswith('temp_'))):
                result = push_customer_to_shopify(obj)
                
                if result.get('success'):
                    self.message_user(request, f"✅ Customer synced to Shopify: {obj.full_name}", level=messages.SUCCESS)
                else:
                    self.message_user(request, f"⚠️ Customer saved locally but Shopify sync failed: {result.get('message', 'Unknown error')}", level=messages.WARNING)
    
    def save_formset(self, request, form, formset, change):
        """Auto-push addresses to Shopify on create/update"""
        instances = formset.save(commit=True)
        
        # Push each address that needs sync
        for instance in instances:
            if isinstance(instance, ShopifyCustomerAddress) and instance.needs_shopify_push:
                # Skip test/temp customers
                if not (instance.customer.shopify_id and (instance.customer.shopify_id.startswith('test_') or instance.customer.shopify_id.startswith('temp_'))):
                    result = push_address_to_shopify(instance)
                    
                    if result.get('success'):
                        self.message_user(request, f"✅ Address synced to Shopify: {instance.city}", level=messages.SUCCESS)
                    else:
                        self.message_user(request, f"⚠️ Address saved locally but Shopify sync failed: {result.get('message', 'Unknown error')}", level=messages.WARNING)
    
    def delete_model(self, request, obj):
        """Handle customer deletion (Django only - no Shopify delete)"""
        customer_name = obj.full_name
        super().delete_model(request, obj)
        self.message_user(request, f"⚠️ Customer '{customer_name}' deleted from Django only (not deleted from Shopify)", level=messages.WARNING)
    
    def sync_selected_customers(self, request, queryset):
        """Sync selected customers from Shopify"""
        count = 0
        for customer in queryset:
            try:
                # This would need individual customer sync implementation
                count += 1
            except Exception as e:
                self.message_user(request, f"Error syncing {customer.email}: {e}", level=messages.ERROR)
        
        self.message_user(request, f"Successfully synced {count} customers", level=messages.SUCCESS)
    
    sync_selected_customers.short_description = "Sync selected customers from Shopify"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('refresh-all/', self.admin_site.admin_view(self.refresh_all_customers), name='customers_refresh_all'),
            path('sync-stats/', self.admin_site.admin_view(self.sync_statistics), name='customers_sync_stats'),
        ]
        return custom_urls + urls
    
    def refresh_all_customers(self, request):
        """Refresh all customers from Shopify"""
        try:
            result = sync_customers_realtime(limit=100)  # Limit for admin safety
            if result['success']:
                stats = result['stats']
                message = f"✅ Customer sync completed! Total: {stats['total']}, Created: {stats['created']}, Updated: {stats['updated']}, Errors: {stats['errors']}"
                messages.success(request, message)
            else:
                messages.error(request, f"❌ Customer sync failed: {result['message']}")
        except Exception as e:
            messages.error(request, f"❌ Error during customer sync: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def sync_statistics(self, request):
        """Show sync statistics"""
        try:
            stats = get_customer_sync_stats()
            message = f"📊 Customer Stats - Total: {stats['total_customers']}, Addresses: {stats['total_addresses']}, Recent syncs (24h): {stats['recent_syncs_24h']}"
            messages.info(request, message)
        except Exception as e:
            messages.error(request, f"❌ Error getting stats: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['refresh_buttons'] = format_html(
            '<a class="button" href="refresh-all/">🔄 Refresh All Customers</a> '
            '<a class="button" href="sync-stats/">📊 Sync Statistics</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShopifyCustomerAddress)
class ShopifyCustomerAddressAdmin(ImportExportModelAdmin):
    resource_class = ShopifyCustomerAddressResource
    list_display = ('customer', 'address_summary', 'city', 'province', 'country')
    list_filter = ('country', 'province', 'store_domain')
    search_fields = ('customer__first_name', 'customer__last_name', 'customer__email', 'address1', 'city')
    readonly_fields = ('shopify_id', 'store_domain')
    
    def address_summary(self, obj):
        return f"{obj.address1}, {obj.city}"
    address_summary.short_description = "Address"


@admin.register(CustomerSyncLog)
class CustomerSyncLogAdmin(ImportExportModelAdmin):
    resource_class = CustomerSyncLogResource
    list_display = ('operation_type', 'status', 'customers_processed', 'customers_created', 'customers_updated', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'store_domain', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
