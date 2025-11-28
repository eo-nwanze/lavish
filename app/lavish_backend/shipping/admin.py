from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ShopifyCarrierService, ShopifyDeliveryProfile, ShopifyDeliveryZone,
    ShopifyDeliveryMethod, ShopifyFulfillmentOrder, ShopifyFulfillmentService,
    ShippingSyncLog
)


@admin.register(ShopifyCarrierService)
class ShopifyCarrierServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'carrier_service_type', 'active_status', 'service_discovery', 'store_domain')
    list_filter = ('active', 'carrier_service_type', 'service_discovery', 'store_domain')
    search_fields = ('name', 'shopify_id', 'callback_url')
    readonly_fields = ('shopify_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'name', 'carrier_service_type')
        }),
        ('Configuration', {
            'fields': ('active', 'service_discovery', 'callback_url', 'format')
        }),
        ('Store Reference', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def active_status(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    active_status.short_description = "Status"


@admin.register(ShopifyDeliveryProfile)
class ShopifyDeliveryProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'active_status', 'default_status', 'zones_count', 'store_domain')
    list_filter = ('active', 'default', 'store_domain')
    search_fields = ('name', 'shopify_id')
    readonly_fields = ('shopify_id',)
    
    def active_status(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    active_status.short_description = "Status"
    
    def default_status(self, obj):
        if obj.default:
            return format_html('<span style="color: blue;">★ Default</span>')
        return '-'
    default_status.short_description = "Default"
    
    def zones_count(self, obj):
        return obj.zones.count()
    zones_count.short_description = "Zones"


@admin.register(ShopifyDeliveryZone)
class ShopifyDeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'countries_list', 'methods_count', 'store_domain')
    list_filter = ('profile', 'store_domain')
    search_fields = ('name', 'shopify_id', 'profile__name')
    readonly_fields = ('shopify_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'name', 'profile')
        }),
        ('Geographic Coverage', {
            'fields': ('countries',)
        }),
        ('Store Reference', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def countries_list(self, obj):
        if obj.countries:
            # Extract country codes from the complex structure
            country_codes = []
            for country in obj.countries[:3]:  # Limit to 3 for display
                if isinstance(country, dict):
                    if 'code' in country and 'countryCode' in country['code']:
                        country_codes.append(country['code']['countryCode'])
                    elif isinstance(country, str):
                        country_codes.append(country)
                else:
                    country_codes.append(str(country))
            return ', '.join(country_codes) if country_codes else 'Complex structure'
        return 'All countries'
    countries_list.short_description = "Countries"
    
    def methods_count(self, obj):
        return obj.methods.count()
    methods_count.short_description = "Methods"


@admin.register(ShopifyDeliveryMethod)
class ShopifyDeliveryMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'method_type', 'profile_name', 'store_domain')
    list_filter = ('method_type', 'zone__profile', 'store_domain')
    search_fields = ('name', 'shopify_id', 'zone__name')
    readonly_fields = ('shopify_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'name', 'zone', 'method_type')
        }),
        ('Delivery Timeframe', {
            'fields': ('min_delivery_date_time', 'max_delivery_date_time'),
            'classes': ('collapse',)
        }),
        ('Store Reference', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def profile_name(self, obj):
        return obj.zone.profile.name
    profile_name.short_description = "Profile"


@admin.register(ShopifyFulfillmentOrder)
class ShopifyFulfillmentOrderAdmin(admin.ModelAdmin):
    list_display = ('shopify_id_short', 'order', 'status', 'request_status', 'location', 'created_at')
    list_filter = ('status', 'request_status', 'location', 'store_domain', 'created_at')
    search_fields = ('shopify_id', 'order__name', 'order__shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'order', 'location')
        }),
        ('Status', {
            'fields': ('status', 'request_status')
        }),
        ('Fulfillment Details', {
            'fields': ('fulfill_at', 'fulfill_by', 'international_duties', 'delivery_method'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Store Reference', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def shopify_id_short(self, obj):
        return obj.shopify_id.split('/')[-1] if '/' in obj.shopify_id else obj.shopify_id
    shopify_id_short.short_description = "ID"


@admin.register(ShopifyFulfillmentService)
class ShopifyFulfillmentServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'handle', 'service_name', 'tracking_support', 'requires_shipping_method', 'store_domain')
    list_filter = ('tracking_support', 'requires_shipping_method', 'include_pending_stock', 'store_domain')
    search_fields = ('name', 'handle', 'shopify_id', 'email')
    readonly_fields = ('shopify_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shopify_id', 'name', 'handle', 'service_name', 'email')
        }),
        ('Capabilities', {
            'fields': ('tracking_support', 'requires_shipping_method', 'include_pending_stock')
        }),
        ('API Configuration', {
            'fields': ('callback_url', 'format'),
            'classes': ('collapse',)
        }),
        ('Store Reference', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShippingSyncLog)
class ShippingSyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'status', 'carriers_processed', 'profiles_processed', 
                    'zones_processed', 'methods_processed', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'store_domain', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
    search_fields = ('operation_type',)
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation_type', 'status')
        }),
        ('Processing Statistics', {
            'fields': ('carriers_processed', 'profiles_processed', 'zones_processed', 
                      'methods_processed', 'fulfillment_orders_processed', 'errors_count')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Error Details', {
            'fields': ('error_details',),
            'classes': ('collapse',)
        }),
        ('Store Reference', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
